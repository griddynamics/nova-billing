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
from nova_billing.usage import dict_add


FLAGS = flags.FLAGS
flags.DEFINE_string("billing_listen", "0.0.0.0",
                    "IP address for Billing API to listen")
flags.DEFINE_integer("billing_listen_port", 8787, "Billing API port")


def datetime_to_str(dt):
    """
    Convert datetime.datetime instance to string.
    Used for JSONization.
    """
    return ("%sZ" % dt.isoformat()) if dt else None


class BillingController(object):
    """
    WSGI application that reads routing information supplied by ``RoutesMiddleware``
    and returns a report.
    """

    @webob.dec.wsgify
    def __call__(self, req):
        """
        Determine period start and stop, ask db api, and return JSON report.
        """
        arg_dict = req.environ['wsgiorg.routing_args'][1]
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
            period_stop = period_start + datetime.timedelta(days=1)
        else:
            if duration.startswith("m"):
                month += 1
                if month > 12:
                    month = 1
                    year += 1
            else:
                year += 1
            period_stop = datetime.datetime(year=year, month=month, day=day)

        queried_project = arg_dict.get("project", None)
        total_statistics = db_api.instances_on_interval(
            period_start, period_stop, queried_project)
        show_instances = not duration.startswith("y") and queried_project
        projects = {}
        if queried_project and not total_statistics.has_key(queried_project):
            total_statistics[queried_project] = {}

        for project_id, project_statistics in total_statistics.items():
            project_dict = {
                "name": project_id,
                "url": "http://%s:%s/projects/%s" %
                       (req.environ["SERVER_NAME"],
                        req.environ["SERVER_PORT"],
                        project_id),
                "instances_count": len(project_statistics),
                "running": 0,
                "usage": {"local_gb": 0, "memory_mb": 0, "vcpus": 0}
            }
            instances = []
            for instance_id, instance_statistics in project_statistics.items():
                project_dict["running"] += instance_statistics["running"]
                dict_add(project_dict["usage"], instance_statistics["usage"])
                if show_instances:
                    instance_dict = {"instance_id": instance_id}
                    for key in "running", "usage":
                        instance_dict[key] = instance_statistics[key]
                    for key in "created_at", "destroyed_at":
                        instance_dict[key] = datetime_to_str(instance_statistics[key])
                    instances.append(instance_dict)

            if show_instances:
                project_dict["instances"] = instances
            for key in project_dict["usage"]:
                project_dict["usage"][key] /= 3600.
            project_dict["running"] /= 3600.
            projects[project_id] = project_dict
        ans_dict = {
            "period_start": datetime_to_str(period_start),
            "period_end": datetime_to_str(period_stop)
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
        mapper.connect(None, "/projects-all/{year}/{month}/{day}",
                        controller=BillingController(),
                        requirements=requirements)
        mapper.connect(None, "/projects-all/{year}/{month}",
                        controller=BillingController(),
                        requirements=requirements)
        mapper.connect(None, "/projects-all/{year}",
                        controller=BillingController(),
                        requirements=requirements)
        super(BillingApplication, self).__init__(mapper)


class Loader(object):
    """This loader is used to load WSGI billing application 
    instead of ``nova.wsgi.Loader`` that loads applications
    from paste configurations."""

    def load_app(self, name):
        return BillingApplication()
