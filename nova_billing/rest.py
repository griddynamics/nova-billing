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
import routes
import routes.middleware

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
    def index(self, req):
        items = [instance_event_dict(event)
               for event in api.instance_event_get(req.GET)]
        return {"items": items}


class BillingApplication(base_wsgi.Router):
    def __init__(self):
        mapper = routes.Mapper()
        mapper.resource("billing", "billing",
                        controller=os_wsgi.Resource(BillingController()))
        super(BillingApplication, self).__init__(mapper)


class Loader(object):
    def load_app(self, name):
        return BillingApplication()
