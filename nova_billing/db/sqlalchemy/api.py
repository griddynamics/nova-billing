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


def instance_life_create(values, session=None):
    instance_life_end(values["instance_id"], values["start_at"])
    instance_life_ref = models.InstanceLife()
    instance_life_ref.update(values)
    instance_life_ref.save(session=session)
    return instance_life_ref


def instance_life_get(self, id, session=None):
    if not session:
        session = get_session()
    result = session.query(models.InstanceLife).filter_by(id=id).first()
    return result


def instance_life_end(instance_id, stop_at, session=None):
    if not session:
        session = get_session()
    session.commit()
    instance_life_ref = session.query(models.InstanceLife).\
        filter_by(instance_id=id, stop_at=None).update({"stop_at": stop_at})


def instance_on_interval(project_id, int_start, int_stop):
    connection = get_session().connection()
    if 1:
      result = connection.execute(
        """
        select instance_id, sum(
            (julianday(case when stop_at is NULL or stop_at > ? then ? else stop_at end) - 
            julianday(case when ? > start_at then ? else start_at end)) * %(instance_types)s.price) as total_price
        from %(instance_life)s inner join %(instance_types)s on (%(instance_life)s.instance_type_id = %(instance_types)s.id) 
        where start_at <= ? and (stop_at is NULL or stop_at >= ?)
        group by instance_id
        """  % {"instance_life": models.InstanceLife.__tablename__,
                "instance_types": models.InstanceTypes.__tablename__},
        int_stop, int_stop,
        int_start, int_start,
        int_stop, int_start)
    else:
     result = connection.execute(
        """
        select instance_id, 
            julianday(stop_at) as total_price
        from %(instance_life)s inner join %(instance_types)s on (%(instance_life)s.instance_type_id = %(instance_types)s.id) 
        where start_at <= ? and (stop_at is NULL or stop_at >= ?)
        
        """  % {"instance_life": models.InstanceLife.__tablename__,
                "instance_types": models.InstanceTypes.__tablename__},
        int_stop, int_start)
    
    for row in result:
        print "%s - %s" % (row["instance_id"], row["total_price"])
    result.close()


def instance_life_filter(filter, session=None):
    if not session:
        session = get_session()
    query = session.query(models.InstanceLife)

    filter_fields = ("user_id",
               "project_id",
               "instance_id",
               "instance_type",
               "event")
    filter_dict = {}
    for field in filter_fields:
        if field in filter:
            filter_dict[field] = filter[field]

    if filter_dict:
        query = query.filter_by(**filter_dict)
    date = _parse_datetime(filter.get("start", None))
    if date:
        query = query.filter(models.InstanceLife.datetime>=date)
    date = _parse_datetime(filter.get("end", None))
    if date:
        query = query.filter(models.InstanceLife.datetime<=date)
    result = query.all()
    return result
