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
Tests for nova_billing.db.sqlalchemy.api
"""

import datetime
import os
import sys

import unittest
import stubout

import routes
import webob

from nova import flags
from nova_billing import amqp
from nova_billing.db.sqlalchemy import api as db_api

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tests


class TestCase(tests.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestCase, self).__init__(*args, **kwargs)
        self.sqlite_file = "/tmp/nova_billing.sqlite"
        flags.FLAGS.billing_sql_connection = "sqlite:///%s" % self.sqlite_file

    def setUp(self):
        """Run before each test method to initialize test environment."""
        super(TestCase, self).setUp()
        self.clear_db()

    instance_id = 1600
    instance_info = {"memory_mb": 2048,
        "project_id": "systenant", "instance_id": instance_id,
        "vcpus": 1, "local_gb": 20}
    instance_segment = {
        "begin_at": datetime.datetime(2011, 1, 1, 0, 0),
        "segment_type": 0}
    volume_id = 42
    volume_info = {
        "allocated_bytes": 2048,
        "project_id": "systenant",
        "volume_id": volume_id
    }
    volume_segment = {
        "begin_at": datetime.datetime(2011, 1, 1, 0, 0),
        "segment_type": 0
    }

    interval_start = datetime.datetime(2010, 1, 1, 0, 0)
    interval_end = datetime.datetime(2011, 1, 1, 0, 1)

    def clear_db(self):
        if os.path.exists(self.sqlite_file):
            os.remove(self.sqlite_file)
        db_api.configure_backend()

    def test_instance_info_create(self):
        instance_info = self.instance_info.copy()
        instance_info_ref = db_api.instance_info_create(instance_info)

        self.assertTrue(hasattr(instance_info_ref, "id"))

    def test_instance_segment(self):
        """ Test instance_info_create and instance_segment_end"""
        instance_info = self.instance_info.copy()
        instance_segment = self.instance_segment.copy()
        instance_info_ref = db_api.instance_info_create(instance_info)
        instance_segment["instance_info_id"] = instance_info_ref.id
        instance_segment_ref = db_api.instance_segment_create(instance_segment)

        self.assertTrue(hasattr(instance_segment_ref, "id"))

        db_api.instance_segment_end(self.instance_id,
            datetime.datetime(2011, 1, 2, 0, 0))

    def test_instance_info_get_latest(self):
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

    def test_volume_info_create(self):
        volume_info = self.volume_info.copy()
        volume_info_ref = db_api.volume_info_create(volume_info)

        self.assertTrue(hasattr(volume_info_ref, "id"))

    def test_volume_segment(self):
        """ Test instance_info_create and instance_segment_end"""
        volume_info = self.volume_info.copy()
        volume_segment = self.volume_segment.copy()
        volume_info_ref = db_api.volume_info_create(volume_info)
        volume_segment["info_id"] = volume_info_ref.id
        volume_segment_ref = db_api.volume_segment_create(volume_segment)

        self.assertTrue(hasattr(volume_segment_ref, "id"))

        db_api.volume_segment_end(self.volume_id,
            datetime.datetime(2011, 1, 2, 0, 0))

    def test_volume_info_get_latest(self):
        volume_segment = self.volume_segment.copy()
        volume_info = self.volume_info.copy()
        volume_info_ref = db_api.volume_info_create(volume_info)
        volume_segment["info_id"] = volume_info_ref.id
        db_api.volume_segment_create(volume_segment)
        db_api.volume_segment_end(self.volume_id,
            datetime.datetime(2011, 1, 2, 0, 0))

        self.assertEqual(volume_info_ref.id,
            db_api.volume_info_get_latest(self.volume_id))

        volume_info_ref = db_api.volume_info_create(volume_info)
        volume_segment["info_id"] = volume_info_ref.id
        self.assertEqual(volume_info_ref.id,
            db_api.volume_info_get_latest(self.volume_id))

    def test_volumes_on_interval(self):
        self.init_volume_segment_data()
        volumes = db_api.volumes_on_interval(
            self.interval_start, self.interval_end)
        self.assertTrue(volumes.has_key("systenant"))

        volume = volumes["systenant"][self.volume_id]
        self.assertTrue(volume.has_key("created_at"))
        self.assertTrue(volume.has_key("destroyed_at"))
        self.assertTrue(volume.has_key("usage"))

        usage_info = volume["usage"]
        self.assertTrue(usage_info.has_key("allocated_bytes"))

        self.assertEquals(usage_info["allocated_bytes"], 122880)

    def test_volumes_on_interval_by_project(self):
        self.init_volume_segment_data()
        volumes = db_api.volumes_on_interval(
            self.interval_start, self.interval_end, "testtenant")
        self.assertFalse(volumes.has_key("systenant"))

    def init_volume_segment_data(self):
        volume_segment = self.volume_segment.copy()
        volume_info = self.volume_info.copy()
        volume_info_ref = db_api.volume_info_create(volume_info)
        volume_segment["info_id"] = volume_info_ref.id
        db_api.volume_segment_create(volume_segment)
        db_api.volume_segment_end(self.volume_id,
            datetime.datetime(2011, 1, 2, 0, 0))

