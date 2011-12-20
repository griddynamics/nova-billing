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

        total_statistics = db_api.instances_on_interval(
            period_start, period_stop, arg_dict.get("project", None))
        show_instances = not duration.startswith("y")
        projects = {}
        for project_id, project_statistics in total_statistics.items():
            instances = {}
            project_dict = {
                "name": project_id,
                "url": "http://%s:%s/projects/%s" %
                    (req.environ["SERVER_NAME"],
                     req.environ["SERVER_PORT"],
                     project_id),
                "instances_count": len(project_statistics),
            }
            project_dict["running"] = 0
            project_dict["usage"] = {"local_gb": 0, "memory_mb": 0, "vcpus": 0}
            for instance_id, instance_statistics in project_statistics.items():
                project_dict["running"] += instance_statistics["running"]
                dict_add(project_dict["usage"], instance_statistics["usage"])
                if show_instances:
                    instance_dict = {"name": instance_id}
                    for key in "running", "usage":
                        instance_dict[key] = instance_statistics[key]
                    for key in "created_at", "destroyed_at":
                        instance_dict[key] = datetime_to_str(instance_statistics[key])
                    instances[instance_id] = instance_dict

            if show_instances:
                project_dict["instances"] = instances
            projects[project_id] = project_dict
        ans_dict = {
            "date": datetime_to_str(period_start),
            "duration": duration,
            "projects": projects
        }
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
        mapper.connect(None, "/projects-all",
                        controller=BillingController(),
                        requirements=requirements)
        super(BillingApplication, self).__init__(mapper)


class Loader(object):
    """This loader is used to load WSGI billing application 
    instead of ``nova.wsgi.Loader`` that loads applications
    from paste configurations."""

    def load_app(self, name):
        return BillingApplication()
