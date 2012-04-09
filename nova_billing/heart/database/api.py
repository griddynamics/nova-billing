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

from datetime import datetime

from sqlalchemy.sql import func, and_, or_
from sqlalchemy.sql.expression import select

from .models import Account, Resource, Segment
from . import db

from nova_billing import utils


def usage_on_interval(period_start, period_stop, account_id=None):
    # FIXME: Fix the doc!
    """
    Retrieve statistics for the given interval [``period_start``, ``period_stop``]. 
    ``account_id=None`` means all projects.

    Example of the returned value:

    .. code-block:: python

        {
            "systenant": {
                12: {
                    "created_at": datetime.datetime(2011, 1, 1),
                    "destroyed_at": datetime.datetime(2011, 1, 2),
                    "usage": {"local_gb": 56, "memory_mb": 89, "vcpus": 4},
                },
                14: {
                    "created_at": datetime.datetime(2011, 1, 4),
                    "destroyed_at": datetime.datetime(2011, 2, 1),
                    "usage": {"local_gb": 18, "memory_mb": 45, "vcpus": 5},
                },
            },
            "tenant12": {
                24: {
                    "created_at": datetime.datetime(2011, 1, 1),
                    "destroyed_at": datetime.datetime(2011, 1, 2),
                    "usage": {"local_gb": 33, "memory_mb": 12, "vcpus": 8},
                },
            }
        }

    :returns: a dictionary where keys are project ids and values are project statistics.
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
            retval[rsrc.account_id] = {}
        try:
            rsrc_descr = rsrc_by_id[rsrc.id]
        except KeyError:
            rsrc_descr = {
                "created_at": None,
                "destroyed_at": None,
                "cost": 0.0,
                "parent_id": rsrc.parent_id,
                "name": rsrc.name,
                "type": rsrc.type,
            }
            retval[rsrc.account_id][rsrc.id] = rsrc_descr
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


def resource_get_or_create(account_id, parent_id, type, name):
    obj = Resource.query.filter_by(
        account_id=account_id,
        parent_id=parent_id,
        type=type,
        name=name).first()
    if obj == None:
        obj = Resource( 
            account_id=account_id,
            parent_id=parent_id,
            type=type,
            name=name)
        db.session.add(obj)
        db.session.commit()
    return obj


def resource_segment_end(resource_id, end_at):
    db.session.execute(Segment.__table__.update().
        values(end_at=end_at).where(
            Segment.resource_id == resource_id))


def account_map():
    return dict(((account.id, account.name)
                 for account in Account.query.all()))


def resource_find(type, name):
    resource_account = (db.session.query(Resource, Account).
        filter(and_(Resource.type == type,
               and_(Resource.name == name,
               Resource.account_id == Account.id))).first())
    return resource_account[0] if resource_account else None
