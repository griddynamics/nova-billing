# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 Grid Dynamics Consulting Services, Inc, All Rights Reserved
#  http://www.griddynamics.com
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
#  FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#  SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#  OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Nova Billing API.
"""

from datetime import datetime

from sqlalchemy.sql import func, and_, or_
from sqlalchemy.sql.expression import select

from nova import flags
from nova import utils

from nova_billing.db.sqlalchemy import models
from nova_billing.db.sqlalchemy.models import InstanceSegment, InstanceInfo
from nova_billing.db.sqlalchemy.session import get_session, get_engine
from nova_billing.billing import SegmentPriceCalculator, total_seconds


FLAGS = flags.FLAGS

def configure_backend():
    """
    Perform backend initialization.
    """
    models.register_models()


def _parse_datetime(dtstr):
    if not dtstr:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.strptime(dtstr, fmt)
        except ValueError:
            pass
    return None


def instance_info_create(values, session=None):
    """
    Create and store an ``InstanceInfo`` object in the database.
    """
    entity_ref = InstanceInfo()
    entity_ref.update(values)
    entity_ref.save(session=session)
    return entity_ref


def instance_info_get(self, id, session=None):
    """
    Get an ``InstanceInfo`` object with the given ``id``.
    """
    if not session:
        session = get_session()
    result = session.query(InstanceInfo).filter_by(id=id).first()
    return result


def instance_segment_create(values, session=None):
    """
    Create and store an ``InstanceSegment`` object in the database.
    """
    entity_ref = InstanceSegment()
    entity_ref.update(values)
    entity_ref.save(session=session)
    return entity_ref


def instance_info_get_latest(instance_id, session=None):
    """
    Get the latest ``InstanceInfo`` object with the given ``instance_id``.
    """
    if not session:
        session = get_session()
    result = session.query(func.max(InstanceInfo.id)).\
        filter_by(instance_id=instance_id).first()
    return result[0]


def instance_segment_end(instance_id, end_at, session=None):
    """
    End all ``InstanceSegment`` objects with  the given ``instance_id``.
    """
    if not session:
        session = get_session()
    session.execute(InstanceSegment.__table__.update().
        values(end_at=end_at).where(InstanceSegment.
        instance_info_id.in_(select([InstanceInfo.id]).
        where(InstanceInfo.instance_id==instance_id))))


def instances_on_interval(period_start, period_stop, project_id=None):
    """
    Retrieve statistics for the given interval [``period_start``, ``period_stop``]. 
    ``project_id=None`` means all projects.

    Example of the returned value:

    .. code-block:: python

        {
                "systenant": {
                     "12": {"created_at": datetime.datetime(2011, 1, 1),
                            "destroyed_at": datetime.datetime(2011, 1, 2),
                            "running": 86400, "price": 2},
                     "14": {"created_at": datetime.datetime(2011, 1, 4),
                            "destroyed_at": datetime.datetime(2011, 2, 1),
                            "running": 2419200, "price": 14},
                },
                "tenant12": {
                     "24": {"created_at": datetime.datetime(2011, 1, 1),
                            "destroyed_at": datetime.datetime(2011, 1, 2),
                            "running": 86400, "price": 12},
                     "30": {"created_at": datetime.datetime(2011, 1, 4),
                            "destroyed_at": datetime.datetime(2011, 2, 1),
                            "running": 2419200, "price": 6},
                }
        }

    :returns: a dictionary where keys are project ids and values are project statistics.
    """
    session = get_session()
    result = session.query(InstanceSegment, InstanceInfo).\
                join(InstanceInfo).\
                filter(InstanceSegment.begin_at < period_stop).\
                filter(or_(InstanceSegment.end_at > period_start,
                           InstanceSegment.end_at == None))
    if project_id:
        result = result.filter(InstanceInfo.project_id == project_id)

    spc = SegmentPriceCalculator()
    retval = {}
    inst_by_id = {}
    for segment, info in result:
        if not retval.has_key(info.project_id):
            retval[info.project_id] = {}
        try:
            inst_descr = inst_by_id[info.instance_id]
        except KeyError:
            inst_descr = {
                "created_at": None,
                "destroyed_at": None,
                "running": 0,
                "price": 0
            }
            retval[info.project_id][info.instance_id] = inst_descr
            inst_by_id[info.instance_id] = inst_descr
        begin_at = max(segment.begin_at, period_start)
        end_at = min(segment.end_at or datetime.utcnow(), period_stop)
        inst_descr["price"] += spc(
            begin_at, end_at, segment.segment_type,
            info.local_gb, info.memory_mb, info.vcpus)

    result = session.query(InstanceSegment,
        func.min(InstanceSegment.begin_at).label("min_start"),
        func.max(InstanceSegment.begin_at).label("max_start"),
        func.max(InstanceSegment.end_at).label("max_stop"),
        InstanceInfo.instance_id).\
        join(InstanceInfo).\
        group_by(InstanceInfo.instance_id).\
        filter(InstanceSegment.begin_at < period_stop).\
        filter(or_(InstanceSegment.end_at > period_start,
                   InstanceSegment.end_at == None))
    if project_id:
        result = result.filter(InstanceInfo.project_id == project_id)

    for row in result:
        inst_descr = inst_by_id.get(row.instance_id, None)
        if not inst_descr:
            continue
        inst_descr["created_at"] = row.min_start
        if row.max_stop is None or row.max_start < row.max_stop:
            inst_descr["destroyed_at"] = row.max_stop
        created_at = max(inst_descr["created_at"], period_start)
        destroyed_at = min(inst_descr["destroyed_at"] or datetime.utcnow(), period_stop)
        inst_descr["running"] = total_seconds(destroyed_at - created_at)

    return retval
