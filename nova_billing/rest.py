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
from nova_billing import nova_utils
from nova_billing import keystone_utils
from nova_billing.version import version_string


FLAGS = flags.FLAGS
flags.DEFINE_string("billing_listen", "0.0.0.0",
                    "IP address for Billing API to listen")
flags.DEFINE_integer("billing_listen_port", 8787, "Billing API port")


nova_projects = nova_utils.NovaProjects()


class BillingController(object):
    """
    WSGI application that reads routing information supplied by ``RoutesMiddleware``
    and returns a report.
    """

    def get_period(self, req, arg_dict):
        if not arg_dict.has_key("year"):
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
                year = now.year
                month = now.month
                day = 1
                duration = "month"
        else:
            year = int(arg_dict["year"])
            duration = "year"
            try:
                month = int(arg_dict["month"])
                duration = "month"
            except KeyError:
                month = 1
            try:
                day = int(arg_dict["day"])
                duration = "day"
            except KeyError:
                day = 1

        period_start = datetime.datetime(year=year, month=month, day=day)
        if duration.startswith("d"):
            period_end = period_start + datetime.timedelta(days=1)
        else:
            if duration.startswith("m"):
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

        if arg_dict.get("action", None) == "index":
            ans_dict = {
                "version": version_string(),
                "application": "nova-billing",
                "urls": {
                    "projects":
                        "http://%s:%s/projects" %
                        (req.environ["SERVER_NAME"],
                         req.environ["SERVER_PORT"]),
                    "projects-all":
                        "http://%s:%s/projects-all" %
                        (req.environ["SERVER_NAME"],
                         req.environ["SERVER_PORT"]),
                }
            }
            return webob.Response(json.dumps(ans_dict),
                         content_type='application/json')

        STATISTICS_NONE = 0
        STATISTICS_SHORT = 1
        STATISTICS_LONG = 2

        queried_project = arg_dict.get("project", None)
        roles = [r.strip()
                 for r in req.headers.get('X_ROLE', '').split(',')]
        is_admin = "Admin" in roles
        if not is_admin and (not queried_project or
                req.headers.get('X_TENANT_NAME', '') != queried_project):
            raise webob.exc.HTTPUnauthorized()

        auth_token = req.headers.get('X_AUTH_TOKEN', '')

        period_start, period_end = self.get_period(req, arg_dict)
        statistics = {"instances": STATISTICS_NONE,
                      "images": STATISTICS_NONE}
        try:
            include = req.GET["include"]
        except KeyError:
            statistics["instances"] = (STATISTICS_LONG
                if period_end - period_start <= datetime.timedelta(days=31)
                    and queried_project
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
            tenant_by_id = dict([(tenant.id, tenant.name) for tenant in tenants])
            reported_projects = (set(nova_projects.get_projects())
                            | set([tenant.name for tenant in tenants]))

            if queried_project:
                if queried_project in reported_projects:
                    reported_projects = set([queried_project])
                else:
                    raise webob.exc.HTTPNotFound()
                queried_tenant_id = '-1'
                for tenant in tenants:
                    if tenant.name == queried_project:
                        queried_tenant_id = tenant.id
                        break
            else:
                queried_tenant_id = None
        else:
            queried_tenant_id = req.headers.get('X_TENANT', '-1')
            reported_projects = set([queried_project])
            tenant_by_id = {queried_tenant_id: queried_project}

        projects = {}
        for project_id in reported_projects:
            projects[project_id] = {
                "name": project_id,
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
                    tenant_by_id, auth_token, queried_tenant_id)
            else:
                total_statistics = db_api.instances_on_interval(
                    period_start, period_end, queried_project)
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
            "period_end": utils.datetime_to_str(period_end)
        }
        if queried_project:
            ans_dict["project"] = projects[queried_project]
        else:
            ans_dict["projects"] = projects
        return webob.Response(json.dumps(ans_dict),
                              content_type='application/json')


class BillingApplication(base_wsgi.Router):
    """
    This application parses HTTP requests and calls ``BillingController``.
    """

    def __init__(self):
        mapper = routes.Mapper()
        requirements = {"year": r"\d\d\d\d", "month": r"\d{1,2}", "day": r"\d{1,2}"}
        mapper.connect(None, "/projects/{project}/{year}/{month}/{day}",
                        controller=BillingController(),
                        requirements=requirements)
        mapper.connect(None, "/projects/{project}/{year}/{month}",
                        controller=BillingController(),
                        requirements=requirements)
        mapper.connect(None, "/projects/{project}/{year}",
                        controller=BillingController(),
                        requirements=requirements)
        mapper.connect(None, "/projects/{project}",
                        controller=BillingController())
        mapper.connect(None, "/projects",
                        controller=BillingController())
        mapper.connect(None, "/projects-all/{year}/{month}/{day}",
                        controller=BillingController(),
                        requirements=requirements)
        mapper.connect(None, "/projects-all/{year}/{month}",
                        controller=BillingController(),
                        requirements=requirements)
        mapper.connect(None, "/projects-all/{year}",
                        controller=BillingController(),
                        requirements=requirements)
        mapper.connect(None, "/projects-all",
                        controller=BillingController())
        mapper.connect(None, "/",
                        controller=BillingController(),
                        action="index")
        super(BillingApplication, self).__init__(mapper)

    @classmethod
    def factory(cls, global_config, **local_config):
        """Simple paste factory, :class:`nova.wsgi.Router` doesn't have one"""
        return cls()
