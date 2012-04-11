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
Tests for nova_billing.rest
"""

import os
import sys
import json
import datetime
import unittest
import stubout
import tempfile

import routes
import webob

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tests


from nova_billing import utils

from nova_billing.heart import app
from nova_billing.heart.database import db


class TestCase(tests.TestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        self.db_fd, self.db_filename = tempfile.mkstemp()
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////" + self.db_filename
        app.config['TESTING'] = True
        self.app_client = app.test_client()
        db.create_all()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_filename)
        super(TestCase, self).tearDown()

    def assertSuccess(self, res):
        self.assertEqual(res.status_code / 100, 2)

    def populate_db(self):
        res = self.app_client.post(
            "/tariff",
            data=json.dumps(self.json_load_from_file("rest.tariff.in.json")),
            content_type=utils.ContentType.JSON)
        self.assertSuccess(res)
        for filename in ("os_amqp.instances.out.json",
                         "os_amqp.local_volumes.out.json"):
            json_out = self.json_load_from_file(filename)
            for event in json_out:
                res = self.app_client.post(
                    "/event",
                    data=json.dumps(event),
                    content_type=utils.ContentType.JSON)
                self.assertSuccess(res)

    def fake_now(self):
        return datetime.datetime(2011, 1, 1)

    def test_version(self):
        res = self.app_client.get("/version")
        self.assertSuccess(res)

    def test_tariff(self):
        res = self.app_client.post(
            "/tariff",
            data=json.dumps(self.json_load_from_file("rest.tariff.in.json")),
            content_type=utils.ContentType.JSON)
        self.assertSuccess(res)
        self.json_check_with_file(json.loads(res.data), 
            "rest.tariff.out.json")

    def test_account(self):
        self.populate_db()
        res = self.app_client.get("/account")
        self.assertSuccess(res)
        self.json_check_with_file(json.loads(res.data), 
                         "rest.account.out.json")
    
    def test_resource(self):
        self.populate_db()
        res = self.app_client.get("/resource")
        self.assertSuccess(res)
        self.json_check_with_file(json.loads(res.data), 
            "rest.resource.out.json")

    def test_resource_filter(self):
        self.populate_db()
        res = self.app_client.get("/resource?rtype=nova/instance")
        self.assertSuccess(res)    
        self.json_check_with_file(json.loads(res.data), 
            "rest.resource_filter.out.json")

    def test_bill(self):
        self.stubs.Set(utils, "now", self.fake_now)        
        self.populate_db()
        res = self.app_client.get("/bill")
        self.assertSuccess(res)
        self.json_check_with_file(json.loads(res.data), 
            "rest.bill.out.json")
        self.stubs.UnsetAll()
