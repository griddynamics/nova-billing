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
Tests for nova_billing.db.sqlalchemy.api
"""


import json
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
