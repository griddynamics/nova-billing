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
REST API for Nova Billing Heart
"""

import json
import datetime

from flask import Flask, request, session, redirect, url_for, \
     jsonify, Response
from werkzeug.exceptions import BadRequest, Unauthorized, NotFound
from . import app

from .database import api as db_api
from .database import db
from .database.models import Account, Resource, Segment, Tariff

from nova_billing import utils
from nova_billing.version import version_string


def request_json():
    ret = request.json
    if ret == None:
        raise BadRequest("Content-Type should be %s" % utils.ContentType.JSON)
    return ret


def to_json(resp):
    return Response(
            json.dumps(resp,
            default=utils.datetime_to_str),
            mimetype=utils.ContentType.JSON)


def check_attrs(rj, attr_list):
    for attr in attr_list:
        if attr not in rj:
            raise BadRequest(
                description="%s must be specified" % attr)


def check_and_get_datatime(rj):
    ret = utils.str_to_datetime(rj.get("datetime", None))
    if not ret:
        raise BadRequest(
            description="valid datetime must be specified")
    return ret


@app.route("/version")
def get_version():
    ans_dict = {
        "version": version_string(),
        "application": "nova-billing",
        "links": [
            [{
                "href": "http://%s:%s/%s" %
                    (request.environ["SERVER_NAME"],
                     request.environ["SERVER_PORT"],
                     url),
                "rel": "self",
            } for url in "bill", "resource", "account", "tariff" ],
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


@app.route("/bill")
def get_bill():
    account_name = request.args.get("account", None)
    if account_name:
        account = Account.query.filter_by(name=account_name).first()
        if account == None:
            raise NotFound()
        account_id = account.id
    else:
        account_id = None

    period_start, period_end = get_period()
    total_statistics = db_api.bill_on_interval(
        period_start, period_end, account_id)

    accounts = db_api.account_map()
    ans_dict = {
        "period_start": period_start,
        "period_end": period_end,
        "bill": [{
            "id": key, "name": accounts.get(key, None), 
            "resources": value
        } for key, value in total_statistics.iteritems()],
    }
    return to_json(ans_dict)


def process_event(rsrc, parent_id, account_id, event_datetime, tariffs):
    """
    linear - saved as a non-negative cost
    fixed - saved with opposite sign (as a non-positive cost)
    fixed=None - closes the segment but does not create a new one
    """
    if not "rtype" in rsrc:
        return
    rsrc_obj = db_api.resource_get_or_create(
        account_id, parent_id,
        rsrc["rtype"], rsrc.get("name", None))
    rsrc_id = rsrc_obj.id

    try:
        attrs = rsrc["attrs"]
    except KeyError:
        pass
    else:
        if rsrc_obj.attrs:
            attrs.update(rsrc_obj.get_attrs())
        rsrc_obj.set_attrs(attrs)
        db.session.merge(rsrc_obj)

    close_segment = True
    if "linear" in rsrc:
        cost = -rsrc["linear"]
    elif "fixed" in rsrc:
        cost = rsrc["fixed"]
    else:
        cost = None
        close_segment = False
    if close_segment:
        db_api.resource_segment_end(rsrc_id, event_datetime)
    if cost is not None:
        obj = Segment(
            resource_id=rsrc_id,
            cost=-cost * tariffs.get(rsrc["rtype"], 1),
            begin_at=event_datetime)
        db.session.add(obj)

    for child in rsrc.get("children", ()):
        process_event(child, rsrc_id,
                         account_id, event_datetime,
                         tariffs)


def process_resource(rsrc, parent_id, account_id):
    if not "rtype" in rsrc:
        return
    rsrc_obj = db_api.resource_get_or_create(
        account_id, parent_id,
        rsrc["rtype"], rsrc.get("name", None))
    rsrc_id = rsrc_obj.id

    try:
        attrs = rsrc["attrs"]
    except KeyError:
        pass
    else:
        rsrc_obj.set_attrs(attrs)
        db.session.merge(rsrc_obj)

    for child in rsrc.get("children", ()):
        process_resource(child, rsrc_id, account_id)


@app.route("/event", methods=["POST"])
def post_event():
    rj = request_json()
    check_attrs(rj, ("rtype", ))
    rj_datetime = check_and_get_datatime(rj)
    try:
        account_name = rj["account"]
    except KeyError:
        resource = db_api.resource_find(rj["rtype"], rj.get("name", None))
        if not resource:
            raise BadRequest(description="account must be specified")
        account_id = resource.account_id
        account_name = resource.name
    else:
        account = db_api.account_get_or_create(account_name)
        account_id = account.id

    tariffs = db_api.tariff_map()
    process_event(rj, None,  account_id, rj_datetime, tariffs)

    db.session.commit()
    return to_json({"account": account_name,
                    "rtype": rj["rtype"],
                    "datetime": rj_datetime,
                    "name": rj.get("name", None)})


@app.route("/tariff", methods=["GET"])
def get_tariff():
    tariffs = db_api.tariff_map()
    return to_json(tariffs)


@app.route("/tariff", methods=["POST"])
def change_tariff():
    rj = request_json()
    check_attrs(rj, ("values", ))
    rj_datetime = check_and_get_datatime(rj)
    migrate = rj.get("migrate", False)

    if migrate:
        old_tariffs = db_api.tariff_map()
    new_tariffs = rj["values"]
    for key, value in new_tariffs.iteritems():
        if isinstance(value, int) or isinstance(value, float):
            db.session.merge(Tariff(rtype=key, multiplier=value))

    if migrate:
        db_api.tariffs_migrate(
            old_tariffs,
            new_tariffs,
            rj_datetime)

    db.session.commit()

    return to_json(new_tariffs)


@app.route("/account", methods=["GET"])
def get_account():
    return to_json([
        {"id": key, "name": value}
        for key, value in db_api.account_map().iteritems()])


@app.route("/resource", methods=["GET"])
def get_resource():
    res = Resource.query
    filter = dict(((fld, request.args[fld]) 
        for fld in ("account_id", "name", "id", "rtype", "parent_id")
        if fld in request.args))
    if filter:
        res = res.filter_by(**filter)
    return to_json([
        {"id": obj.id,
         "name": obj.name,
         "rtype": obj.rtype,
         "account_id": obj.account_id,
         "parent_id": obj.parent_id,
         "attrs": obj.get_attrs(),
        } for obj in res.all()
    ])


@app.route("/resource", methods=["POST"])
def post_resource():
    rj = request_json()
    check_attrs(rj, ("rtype", ))
    try:
        account_name = rj["account"]
    except KeyError:
        resource = db_api.resource_find(rj["rtype"], rj.get("name", None))
        if not resource:
            raise BadRequest(description="account must be specified")
        account_id = resource.account_id
        account_name = resource.name
    else:
        account = db_api.account_get_or_create(account_name)
        account_id = account.id

    process_resource(rj, None,  account_id)

    db.session.commit()
    return to_json({"account": account_name,
                    "rtype": rj["rtype"],
                    "name": rj.get("name", None)})
