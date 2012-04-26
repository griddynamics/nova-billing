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
Tests for os-amqp
"""


import os
import sys
import json
import datetime
import unittest
import stubout


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tests

from nova_billing.os_amqp import amqp
from nova_billing.os_amqp import instances


class TestCase(tests.TestCase):
    day = 1
    requests = []

    def setUp(self):
        super(TestCase, self).setUp()
        self.stubs.Set(amqp.Service, "__init__", lambda self: None)

    def fake_get_event_datetime(self, body):
        self.day += 1
        return datetime.datetime(2011, 1, self.day)

    def fake_event(self, req):
        self.requests.append(req)

    def fake_get_instance_flavor(self, instance_id):
        return self.flavor

    def test_amqp_instances(self):
        self.day = 1
        self.requests = []
        service = amqp.Service()
        
        self.stubs.Set(service.billing_heart, "event", self.fake_event)
        self.stubs.Set(service, "get_event_datetime", self.fake_get_event_datetime)
        self.stubs.Set(instances, "get_instance_flavor", self.fake_get_instance_flavor)

        json_in = self.json_load_from_file("os_amqp.instances.in.json") 
        run_instance_body = json_in["run"]
        any_instance_body = json_in["any"]
        self.flavor = run_instance_body["args"]["request_spec"]["instance_type"]

        service.process_event(run_instance_body, None)
        for method in ("stop_instance", "start_instance",
                       "pause_instance", "unpause_instance",
                       "suspend_instance", "resume_instance",
                       "terminate_instance"):
            any_instance_body["method"] = method
            service.process_event(any_instance_body, None)
        service.process_event(run_instance_body, None)
        for method in ("stop_instance", "start_instance"):
            any_instance_body["method"] = method
            service.process_event(any_instance_body, None)

        self.stubs.UnsetAll()
        self.json_check_with_file(self.requests, 
            "os_amqp.instances.out.json")

    def test_amqp_local_volumes(self):
        self.day = 1
        self.requests = []
        service = amqp.Service()
        
        self.stubs.Set(service.billing_heart, "event", self.fake_event)
        self.stubs.Set(service, "get_event_datetime", self.fake_get_event_datetime)
        self.stubs.Set(instances, "get_instance_flavor", self.fake_get_instance_flavor)

        json_in = self.json_load_from_file("os_amqp.local_volumes.in.json")
        
        for event in json_in:
            service.process_event(event, None)

        self.stubs.UnsetAll()
        self.json_check_with_file(self.requests,
            "os_amqp.local_volumes.out.json")
