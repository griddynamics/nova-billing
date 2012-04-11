# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Nova Billing
#    Copyright (C) GridDynamics Openstack Core Team, GridDynamics
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Nova Billing API.
"""

from itertools import repeat
from datetime import datetime

from sqlalchemy.sql import func, and_, or_
from sqlalchemy.sql.expression import text

from .models import Account, Resource, Segment, Tariff
from . import db

from nova_billing import utils


def bill_on_interval(period_start, period_stop, account_id=None):
    """
    Retrieve statistics for the given interval [``period_start``, ``period_stop``]. 
    ``account_id=None`` means all accounts.

    Example of the returned value:

    .. code-block:: python

        {
            1: [
                {
                    "name": "16", 
                    "rtype": "nova/instance", 
                    "created_at": "2011-01-02T00:00:00Z", 
                    "destroyed_at": null, 
                    "parent_id": null, 
                    "cost": 0.0, 
                    "id": 1
                }, 
                {
                    "name": null, 
                    "rtype": "local_gb", 
                    "created_at": "2011-01-02T00:00:00Z", 
                    "destroyed_at": null, 
                    "parent_id": 1, 
                    "cost": 1200.0, 
                    "id": 2
                }, 
                {
                    "name": null, 
                    "rtype": "memory_mb", 
                    "created_at": "2011-01-02T00:00:00Z", 
                    "destroyed_at": null, 
                    "parent_id": 1, 
                    "cost": 380928.0, 
                    "id": 3
                }
            ]
        }

    :returns: a dictionary where keys are account ids and values are billing lists.
    """
    result = (db.session.query(Segment, Resource).
                join(Resource).
                filter(Segment.begin_at < period_stop).
                filter(or_(Segment.end_at > period_start,
                           Segment.end_at == None)))
    if account_id:
        result = result.filter(Resource.account_id == account_id)
    
    retval = {}
    rsrc_by_id = {}
    now = datetime.utcnow()
    for segment, rsrc in result:
        if not retval.has_key(rsrc.account_id):
            retval[rsrc.account_id] = []
        try:
            rsrc_descr = rsrc_by_id[rsrc.id]
        except KeyError:
            rsrc_descr = {
                "id": rsrc.id,
                "created_at": None,
                "destroyed_at": None,
                "cost": 0.0,
                "parent_id": rsrc.parent_id,
                "name": rsrc.name,
                "rtype": rsrc.rtype,
            }
            retval[rsrc.account_id].append(rsrc_descr)
            rsrc_by_id[rsrc.id] = rsrc_descr
        begin_at = max(segment.begin_at, period_start)
        end_at = min(segment.end_at or now, period_stop)
        rsrc_descr["cost"] += utils.cost_add(segment.cost, begin_at, end_at)

    result = (db.session.query(Segment,
        func.min(Segment.begin_at).label("min_start"),
        func.max(Segment.begin_at).label("max_start"),
        func.max(Segment.end_at).label("max_stop"),
        Resource.id).
        join(Resource).
        group_by(Resource.id).
        filter(Segment.begin_at < period_stop).
        filter(or_(Segment.end_at > period_start,
                   Segment.end_at == None)))
    if account_id:
        result = result.filter(Resource.account_id == account_id)

    for row in result:
        rsrc_descr = rsrc_by_id.get(row.id, None)
        if not rsrc_descr:
            continue
        rsrc_descr["created_at"] = row.min_start
        if row.max_stop is None or row.max_start < row.max_stop:
            rsrc_descr["destroyed_at"] = row.max_stop

    return retval


def account_get_or_create(name):
    obj = Account.query.filter_by(name=name).first()
    if obj == None:
        obj = Account(name=name)
        db.session.add(obj)
        db.session.commit()
    return obj


def resource_get_or_create(account_id, parent_id, rtype, name):
    obj = Resource.query.filter_by(
        account_id=account_id,
        parent_id=parent_id,
        rtype=rtype,
        name=name).first()
    if obj == None:
        obj = Resource( 
            account_id=account_id,
            parent_id=parent_id,
            rtype=rtype,
            name=name)
        db.session.add(obj)
        db.session.commit()
    return obj


def resource_segment_end(resource_id, end_at):
    db.session.execute(Segment.__table__.update().
        values(end_at=end_at).where(
            Segment.resource_id == resource_id))


def account_map():
    return dict(((obj.id, obj.name)
                 for obj in Account.query.all()))


def tariff_map():
    return dict(((obj.rtype, obj.multiplier)
                 for obj in Tariff.query.all()))


def resource_find(rtype, name):
    resource_account = (db.session.query(Resource, Account).
        filter(and_(Resource.rtype == rtype,
               and_(Resource.name == name,
               Resource.account_id == Account.id))).first())
    return resource_account[0] if resource_account else None


def tariffs_migrate(old_tariffs, new_tariffs, event_datetime):
    new_tariffs = dict(
        ((key, float(value))
         for key, value in new_tariffs.iteritems()
         if value != old_tariffs.get(key, 1.0)))
    connection = db.session.connection()
    for rtype in new_tariffs:
        old_t = old_tariffs.get(rtype, 1.0)
        if old_t < 0:
            old_t = 1.0
        
        connection.execute(
            "insert into %(segment)s"
            " (resource_id, cost, begin_at, end_at)"
            " select resource_id, cost * ?, ?, NULL"
            " from %(segment)s, %(resource)s"
            " where end_at is NULL "
            " and %(segment)s.resource_id = %(resource)s.id"
            " and %(resource)s.rtype = ?" %
            {"segment": Segment.__tablename__,
             "resource": Resource.__tablename__},
            new_tariffs[rtype] / old_t,
            event_datetime,
            rtype)

    changed_keys = new_tariffs.keys()
    max_args = 32
    for i in xrange(1 + len(changed_keys) / max_args):
        partial_keys = changed_keys[i * max_args:(i + 1) * max_args] 
        connection.execute(
            "update %(segment)s"
            " set end_at = ?"
            " where end_at is NULL"
            " and begin_at != ?"
            " and resource_id in"
            " (select id from %(resource)s where rtype in (%(type_list)s))" %
            {"segment": Segment.__tablename__,
             "resource": Resource.__tablename__,
             "type_list": ", ".join(repeat("?", len(partial_keys)))},
            event_datetime, event_datetime,
            *partial_keys)
