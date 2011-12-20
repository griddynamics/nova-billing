# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Openstack Nova Billing
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
Tests for nova_billing.db.sqlalchemy.api
"""

import datetime
import os

import unittest
import stubout

import routes
import webob

from nova import flags
from nova_billing import amqp
from nova_billing.db.sqlalchemy import api as db_api


class TestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestCase, self).__init__(*args, **kwargs)
        self.sqlite_file = "/tmp/nova_billing.sqlite"
        flags.FLAGS.billing_sql_connection = "sqlite:///%s" % self.sqlite_file

    def setUp(self):
        """Run before each test method to initialize test environment."""
        super(TestCase, self).setUp()
        self.stubs = stubout.StubOutForTesting()

    instance_id = 1600
    instance_info = {"memory_mb": 2048,
        "project_id": "systenant", "instance_id": instance_id,
        "vcpus": 1, "local_gb": 20}
    instance_segment = {
        "begin_at": datetime.datetime(2011, 1, 1, 0, 0),
        "segment_type": 0}

    interval_start = datetime.datetime(2010, 1, 1, 0, 0)
    interval_end = datetime.datetime(2011, 1, 1, 0, 1)

    def clear_db(self):
        os.remove(self.sqlite_file)
        db_api.configure_backend()

    def test_instance_info_create(self):
        self.clear_db()

        instance_info = self.instance_info.copy()
        instance_info_ref = db_api.instance_info_create(instance_info)

        self.assertTrue(hasattr(instance_info_ref, "id"))

    def test_instance_segment(self):
        """ Test instance_info_create and instance_segment_end"""
        self.clear_db()

        instance_info = self.instance_info.copy()
        instance_segment = self.instance_segment.copy()
        instance_info_ref = db_api.instance_info_create(instance_info)
        instance_segment["instance_info_id"] = instance_info_ref.id
        instance_segment_ref = db_api.instance_segment_create(instance_segment)

        self.assertTrue(hasattr(instance_segment_ref, "id"))

        db_api.instance_segment_end(self.instance_id,
            datetime.datetime(2011, 1, 2, 0, 0))

    def test_instance_info_get_latest(self):
        self.clear_db()

        instance_segment = self.instance_segment.copy()
        instance_info = self.instance_info.copy()
        instance_info_ref = db_api.instance_info_create(instance_info)
        instance_segment["instance_info_id"] = instance_info_ref.id
        db_api.instance_segment_create(instance_segment)
        db_api.instance_segment_end(self.instance_id,
            datetime.datetime(2011, 1, 2, 0, 0))

        self.assertEqual(instance_info_ref.id,
            db_api.instance_info_get_latest(self.instance_id))

        instance_info_ref = db_api.instance_info_create(instance_info)
        instance_segment["instance_info_id"] = instance_info_ref.id
        self.assertEqual(instance_info_ref.id,
            db_api.instance_info_get_latest(self.instance_id))

    def test_instances_on_interval(self):
        self.init_instance_segment_data()
        instances = db_api.instances_on_interval(
            self.interval_start, self.interval_end)
        self.assertTrue(instances.has_key("systenant"))

        instance = instances["systenant"][self.instance_id]
        self.assertTrue(instance.has_key("created_at"))
        self.assertTrue(instance.has_key("destroyed_at"))
        self.assertTrue(instance.has_key("running"))
        self.assertTrue(instance.has_key("usage"))

        usage_info = instance["usage"]
        self.assertTrue(usage_info.has_key("local_gb"))
        self.assertTrue(usage_info.has_key("memory_mb"))
        self.assertTrue(usage_info.has_key("vcpus"))

        self.assertEquals(usage_info["vcpus"], 60)
        self.assertEquals(usage_info["memory_mb"], 122880)
        self.assertEquals(usage_info["local_gb"], 1200)

    def test_instances_on_interval_by_project(self):
        self.init_instance_segment_data()
        instances = db_api.instances_on_interval(
            self.interval_start, self.interval_end, "testtenant")
        self.assertFalse(instances.has_key("systenant"))

    def init_instance_segment_data(self):
        instance_segment = self.instance_segment.copy()
        instance_info = self.instance_info.copy()
        instance_info_ref = db_api.instance_info_create(instance_info)
        instance_segment["instance_info_id"] = instance_info_ref.id
        db_api.instance_segment_create(instance_segment)
        db_api.instance_segment_end(self.instance_id,
            datetime.datetime(2011, 1, 2, 0, 0))

