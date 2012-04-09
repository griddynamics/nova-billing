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
REST API for Nova Billing
"""

import json
import datetime

from flask import Flask, request, session, redirect, url_for, \
     jsonify, Response
from werkzeug.exceptions import BadRequest, Unauthorized, NotFound
from . import app

from .database import api as db_api
from .database import db
from .database.models import Account, Resource, Segment

from nova_billing import utils 
from nova_billing.version import version_string


def to_json(resp):
    return Response(
            json.dumps(resp, 
            default=lambda obj: obj.isoformat() 
                if isinstance(obj, datetime.datetime) else None),
            mimetype=utils.ContextType.JSON)


@app.route("/version")
def get_version():
    ans_dict = {
        "version": version_string(),
        "application": "nova-billing",
        "links": [
            {
                "href": "http://%s:%s/usage" %
                    (request.est.environ["SERVER_NAME"],
                     request.est.environ["SERVER_PORT"]),
                "rel": "self",
            },
        ],
    }
    
    return jsonify(ans_dict)


def get_period():
    if not request.args.has_key("time_period"):
        if "period_start" in request.args:
            period_start = utils.str_to_datetime(request.args["period_start"])
            try:
                period_end = utils.str_to_datetime(request.args["period_end"])
            except KeyError:
                raise BadRequest(description="period_end is request.ired")
            if not (period_start and period_end):
                raise BadRequest(
                    description="date should be in ISO 8601 format of YYYY-MM-DDThh:mm:ssZ")
            if period_start >= period_end:
                raise BadRequest(
                    description="period_start must be less than period_end")
            return period_start, period_end
        else:
            now = utils.now()
            date_args = (now.year, now.month, 1)
            date_incr = 1
    else:
        time_period_splitted = request.args["time_period"].split("-", 2)
        date_args = [1, 1, 1]
        for i in xrange(min(2, len(time_period_splitted))):
            try:
                date_args[i] = int(time_period_splitted[i])
            except ValueError:
                raise BadRequest(
                    description="invalid time_period `%s'" % request.args["time_period"])
        date_incr = len(time_period_splitted) - 1

    period_start = datetime.datetime(*date_args)
    if date_incr == 2:
        period_end = period_start + datetime.timedelta(days=1)
    else:
        year, month, day = date_args
        if date_incr == 1:
            month += 1
            if month > 12:
                month = 1
                year += 1
        else:
            year += 1
        period_end = datetime.datetime(year=year, month=month, day=day)
    return period_start, period_end


@app.route("/usage")
def get_usage(): 
    account_name = request.args.get("account", None)
    if account_name: 
        account = Account.query.filter_by(name=account_name).first()
        if account == None:
            raise NotFound()
        account_id = account.id
    else:
        account_id = None

    period_start, period_end = get_period()
    total_statistics = db_api.usage_on_interval(
        period_start, period_end, account_id)

    accounts = db_api.account_map()
    ans_dict = {
        "period_start": period_start,
        "period_end": period_end,
        "usage": dict((
            (accounts.get(key, key), value) 
            for key, value in total_statistics.iteritems())),
    }
    return to_json(ans_dict)


def request_json():
    ret = request.json
    if ret == None:
        raise BadRequest()
    return ret


def process_resource(rsrc, parent_id, account_id, event_datetime):
    if not "type" in rsrc:
        return
    rsrc_obj = db_api.resource_get_or_create(
        account_id, parent_id,
        rsrc["type"], rsrc.get("name", None))
    rsrc_id = rsrc_obj.id
    db_api.resource_segment_end(rsrc_id, event_datetime)
    if "cost" in rsrc:
        cost = rsrc["cost"]
    elif "fixed" in rsrc:
        cost = -rsrc["fixed"]
    else:
        cost = 0
    if cost is not None:
        obj = Segment(resource_id=rsrc_id,
            cost=cost, begin_at=event_datetime)
        db.session.add(obj)
    for child in rsrc.get("children", ()):
        process_resource(child, rsrc_id, account_id, event_datetime)


@app.route("/event", methods=["POST"])
def post_event():
    rj = request_json()
    try:
        account_name = rj["account"]
    except KeyError:
        resource = db_api.resource_find(rj.get("type"), rj.get("name"))
        if not resource:
            raise BadRequest(description="account must be specified")
        account_id = resource.account_id
    else:
        account = db_api.account_get_or_create(account_name)
        account_id = account.id

    process_resource(rj, None, account_id,
                     utils.str_to_datetime(rj["datetime"]))

    db.session.commit()
    return Response("hello")
