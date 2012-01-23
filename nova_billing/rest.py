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
import webob
import routes
import routes.middleware
import datetime

from nova import flags
from nova import wsgi as base_wsgi
from nova.api.openstack import wsgi as os_wsgi

from nova_billing.db import api as db_api
from nova_billing import utils
from nova_billing import glance_utils
from nova_billing import keystone_utils
from nova_billing.version import version_string


FLAGS = flags.FLAGS
flags.DEFINE_string("billing_listen", "0.0.0.0",
                    "IP address for Billing API to listen")
flags.DEFINE_integer("billing_listen_port", 8787, "Billing API port")


class VersionFilter(object):
    """
    Filter returning version for "/" request
    """
    def __init__(self, application):
        self.application = application

    @webob.dec.wsgify
    def __call__(self, req):
        if req.environ.get("PATH_INFO", "/") == "/":
            ans_dict = {
                "version": version_string(),
                "application": "nova-billing",
                "links": [
                    {
                        "href": "http://%s:%s/projects" %
                            (req.environ["SERVER_NAME"],
                             req.environ["SERVER_PORT"]),
                        "rel": "self",
                    },
                ],
            }
            return webob.Response(json.dumps(ans_dict),
                         content_type='application/json')

        return req.get_response(self.application)

    @classmethod
    def factory(cls, global_config, **local_config):
        def filter(app):
            return cls(app)

        return filter


class BillingController(object):
    """
    WSGI application that reads routing information supplied by ``RoutesMiddleware``
    and returns a report.
    """

    def get_period(self, req):
        if not req.GET.has_key("time_period"):
            if "period_start" in req.GET:
                period_start = utils.str_to_datetime(req.GET["period_start"])
                try:
                    period_end = utils.str_to_datetime(req.GET["period_end"])
                except KeyError:
                    raise webob.exc.HTTPBadRequest(explanation="period_end is required")
                if not (period_start and period_end):
                    raise webob.exc.HTTPBadRequest(
                        explanation="date should be in ISO 8601 format of YYYY-MM-DDThh:mm:ssZ")
                if period_start >= period_end:
                    raise webob.exc.HTTPBadRequest(
                        explanation="period_start must be less than period_end")
                return period_start, period_end
            else:
                now = utils.now()
                date_args = (now.year, now.month, 1)
                date_incr = 1
        else:
            time_period_splitted = req.GET["time_period"].split("-", 2)
            date_args = [1, 1, 1]
            for i in xrange(min(2, len(time_period_splitted))):
                try:
                    date_args[i] = int(time_period_splitted[i])
                except ValueError:
                    raise webob.exc.HTTPBadRequest(
                        explanation="invalid time_period `%s'" % req.GET["time_period"])
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

    @webob.dec.wsgify
    def __call__(self, req):
        """
        Determine period start and stop, ask db api, and return JSON report.
        """
        arg_dict = req.environ['wsgiorg.routing_args'][1]

        STATISTICS_NONE = 0
        STATISTICS_SHORT = 1
        STATISTICS_LONG = 2

        queried_tenant_id = arg_dict.get("project_id", None)
        roles = [r.strip()
                 for r in req.headers.get('X_ROLE', '').split(',')]
        is_admin = "Admin" in roles
        if not is_admin:
            if queried_tenant_id:
                if req.headers.get('X_TENANT_ID', '') != queried_tenant_id:
                    raise webob.exc.HTTPUnauthorized()
            else:
                queried_tenant_id = req.headers.get('X_TENANT_ID', '-1')

        auth_token = req.headers.get('X_AUTH_TOKEN', '')

        period_start, period_end = self.get_period(req)
        statistics = {"instances": STATISTICS_NONE,
                      "images": STATISTICS_NONE}
        try:
            include = req.GET["include"]
        except KeyError:
            statistics["instances"] = (STATISTICS_LONG
                if period_end - period_start <= datetime.timedelta(days=31)
                    and queried_tenant_id
                else STATISTICS_SHORT)
        else:
            include = include.strip(",")
            for key in "images", "instances":
                if (key + "-long") in include:
                    statistics[key] = STATISTICS_LONG
                elif key in include:
                    statistics[key] = STATISTICS_SHORT

        if is_admin:
            tenants = keystone_utils.KeystoneTenants().\
                    get_tenants(auth_token)
            reported_projects = set([tenant.id for tenant in tenants])
            tenant_name_by_id = dict([(tenant.id, tenant.name) for tenant in tenants])
            if queried_tenant_id:
                if queried_tenant_id in reported_projects:
                    reported_projects = set([queried_tenant_id])
                else:
                    raise webob.exc.HTTPNotFound()
        else:
            reported_projects = set([queried_tenant_id])
            tenant_name_by_id = {queried_tenant_id:
                                 req.headers.get('X_TENANT_NAME', None)}

        projects = {}
        for project_id in reported_projects:
            projects[project_id] = {
                "id": str(project_id),
                "name": tenant_name_by_id[project_id],
                "url": "http://%s:%s/projects/%s" %
                       (req.environ["SERVER_NAME"],
                        req.environ["SERVER_PORT"],
                        project_id),
            }
        now = utils.now()
        for statistics_key in "images", "instances":
            if not statistics[statistics_key]:
                continue
            show_items = statistics[statistics_key] == STATISTICS_LONG
            if statistics_key == "images":
                total_statistics = glance_utils.images_on_interval(
                    period_start, period_end,
                    auth_token, queried_tenant_id)
            else:
                total_statistics = db_api.instances_on_interval(
                    period_start, period_end, queried_tenant_id)
            for project_id in projects:
                project_statistics = total_statistics.get(project_id, {})
                project_dict = {
                    "count": len(project_statistics),
                }
                project_usage = {}
                items = []
                for item_id, item_statistics in project_statistics.items():
                    utils.dict_add(project_usage, item_statistics["usage"])
                    if show_items:
                        lifetime = utils.total_seconds(
                            min(item_statistics["destroyed_at"] or now, period_end) -
                            max(item_statistics["created_at"], period_start))
                        item_dict = {
                            "id": item_id,
                            "lifetime_sec": lifetime,
                            "usage": utils.usage_to_hours(item_statistics["usage"]),
                            "name": item_statistics.get("name", None),
                        }
                        for key in "created_at", "destroyed_at":
                            item_dict[key] = utils.datetime_to_str(item_statistics[key])
                        items.append(item_dict)

                if show_items:
                    project_dict["items"] = items
                project_dict["usage"] = utils.usage_to_hours(project_usage)
                projects[project_id][statistics_key] = project_dict

        ans_dict = {
            "period_start": utils.datetime_to_str(period_start),
            "period_end": utils.datetime_to_str(period_end),
            "projects": projects.values(),
        }
        return webob.Response(json.dumps(ans_dict),
                              content_type='application/json')


class BillingApplication(base_wsgi.Router):
    """
    This application parses HTTP requests and calls ``BillingController``.
    """

    def __init__(self):
        mapper = routes.Mapper()
        mapper.connect(None, "/projects/{project_id}",
                       controller=BillingController())
        mapper.connect(None, "/projects",
                       controller=BillingController())
        super(BillingApplication, self).__init__(mapper)

    @classmethod
    def factory(cls, global_config, **local_config):
        """Simple paste factory, :class:`nova.wsgi.Router` doesn't have one"""
        return cls()
