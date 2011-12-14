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

from nova_billing.db.sqlalchemy import models
from nova_billing.db.sqlalchemy.session import get_session, get_engine

from sqlalchemy.sql import func, and_, or_

from nova import flags
from nova import utils


FLAGS = flags.FLAGS


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
    instance_info_ref = models.InstanceInfo()
    instance_info_ref.update(values)
    instance_info_ref.save(session=session)
    return instance_info_ref


def instance_info_get(self, id, session=None):
    if not session:
        session = get_session()
    result = session.query(models.InstanceInfo).filter_by(id=id).first()
    return result


def instance_segment_create(values, session=None):
    instance_segment_ref = models.InstanceSegment()
    instance_segment_ref.update(values)
    instance_segment_ref.save(session=session)
    return instance_segment_ref


def instance_info_get_latest(instance_id, session=None):
    if not session:
        session = get_session()
    result = session.query(func.max(models.InstanceInfo.id)).\
        filter_by(instance_id=instance_id).first()
    return result[0]


def instance_segment_end(instance_id, end_at, session=None):
    if not session:
        session = get_session()
    connection = get_session().connection()
    connection.execute("""
        update %(instance_segment)s set end_at = ?
        where instance_info_id in
        (select id from %(instance_info)s where instance_id = ?)
        """ %
        {"instance_segment": models.InstanceSegment.__tablename__,
         "instance_info": models.InstanceInfo.__tablename__},
        end_at,
        instance_id
    )


def instance_segment_on_interval(period_start, period_stop, project_id=None):
    result = session.query(models.InstanceSegment).\
        filter(and_(models.InstanceSegment.begin_at <= period_stop,
                    or_(models.InstanceSegment.end_at is None,
                        models.InstanceSegment.end_at >= period_start)))
    return result


def instances_on_interval(period_start, period_stop, project_id=None):
    """
    project_id=None means all projects
    returns dict(key = project_id,
                 value = dict(
                     key=instance_id,
                     value=dict{"created_at", "destroyed_at", "running", "existing", "price"}
                     )
                )
    """
    connection = get_session().connection()
    if 1:
      result = connection.execute(
        """
        select instance_id, sum(
            (julianday(case when stop_at is NULL or stop_at > ? then ? else stop_at end) - 
            julianday(case when ? > start_at then ? else start_at end)) * %(instance_types)s.price) as total_price
        from %(instance_info)s inner join %(instance_types)s on (%(instance_info)s.instance_type_id = %(instance_types)s.id) 
        where start_at <= ? and (stop_at is NULL or stop_at >= ?)
        group by instance_id
        """  % {"instance_info": models.InstanceInfo.__tablename__,
                "instance_types": models.InstanceTypes.__tablename__},
        int_stop, int_stop,
        int_start, int_start,
        int_stop, int_start)
    else:
     result = connection.execute(
        """
        select instance_id, 
            julianday(stop_at) as total_price
        from %(instance_info)s inner join %(instance_types)s on (%(instance_info)s.instance_type_id = %(instance_types)s.id) 
        where start_at <= ? and (stop_at is NULL or stop_at >= ?)
        
        """  % {"instance_info": models.InstanceInfo.__tablename__,
                "instance_types": models.InstanceTypes.__tablename__},
        int_stop, int_start)
    
    for row in result:
        print "%s - %s" % (row["instance_id"], row["total_price"])
    result.close()
