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

from nova_billing.db.sqlalchemy import api


FLAGS = flags.FLAGS
flags.DEFINE_string("billing_listen", "0.0.0.0",
                    "IP address for Billing API to listen")
flags.DEFINE_integer("billing_listen_port", 8787, "Billing API port")


def instance_event_dict(instance_event):
    ret = {"datetime": str(instance_event.datetime)}
    for attr in ("user_id",
               "project_id",
               "instance_id",
               "instance_type",
               "event"):
        ret[attr] = getattr(instance_event, attr)
    return ret


class BillingController(object):
    """
    WSGI app that reads routing information supplied by RoutesMiddleware
    """

    @webob.dec.wsgify
    def __call__(self, req):
        """
        Call the method specified in req.environ by RoutesMiddleware.
        """
        arg_dict = req.environ['wsgiorg.routing_args'][1]
        print arg_dict
        
        year = int(arg_dict["year"])
        granularity = "y"
        try:
            month = int(arg_dict["month"])
            granularity = "m"
        except KeyError:
            month = 1
        try:
            day = int(arg_dict["day"])
            granularity = "d"
        except KeyError:
            day = 1

        int_start = datetime.datetime(year=year, month=month, day=day)
        if granularity == "d":
            int_stop = int_start + datetime.timedelta(days=1)
        else:
            if granularity == "m":
                month += 1
                if month > 12:
                    month = 1
                    year += 1
            else:
                year += 1
            int_stop = datetime.datetime(year=year, month=month, day=day)
        print "%s - %s" % (int_start, int_stop)
        api.instance_on_interval(None, int_start, int_stop)
        return "hello\n"


class BillingApplication(base_wsgi.Router):
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
    def load_app(self, name):
        return BillingApplication()
