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
Tests for nova_billing.amqp
"""


import os
import sys
import datetime

import nova_billing.ampq_listener
from nova_billing.interceptors import instance, local_volume
from nova_billing import utils
from nova_billing.db import api as db_api
from nova_billing.db.sqlalchemy import models
from nova_billing import novaclient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tests

class FakeDbApi(object):

    class FakeInfo(object):
        def __init__(self, **args):
            self.__dict__ = args

    def __init__(self):
        self.db = { "instance_info": [], "instance_segment": [], "volume_info": [], "volume_segment": []}

    def instance_info_create(self, values, session=None):
        values["id"] = len(self.db["instance_info"]) + 1
        self.db["instance_info"].append(values)
        entity_ref = models.InstanceInfo()
        entity_ref.update(values)
        return entity_ref

    def instance_segment_create(self, values, session=None):
        values["id"] = len(self.db["instance_segment"]) + 1
        values["end_at"] = values.get("end_at", None)
        self.db["instance_segment"].append(values)
        entity_ref = models.InstanceSegment()
        entity_ref.update(values)
        return entity_ref

    def instance_info_get(self, instance_id, session=None):
        for instance_info in reversed(self.db["instance_info"]):
            if instance_info["instance_id"] == instance_id:
                return self.FakeInfo(**instance_info)

    def instance_info_get_latest(self, instance_id, session=None):
        return self.instance_info_get(instance_id).id

    def instance_segment_end(self, instance_id, end_at, session=None):
        for segment in self.db["instance_segment"]:
            if not segment["end_at"]:
                segment["end_at"] = end_at

    def volume_info_create(self, values, session=None):
        values["id"] = len(self.db["volume_info"]) + 1
        self.db["volume_info"].append(values)
        entity_ref = models.VolumeInfo()
        entity_ref.update(values)
        return entity_ref

    def volume_segment_create(self, values, session=None):
        values["id"] = len(self.db["volume_segment"]) + 1
        values["end_at"] = values.get("end_at", None)
        self.db["volume_segment"].append(values)
        entity_ref = models.VolumeSegment()
        entity_ref.update(values)
        return entity_ref

    def volume_info_get(self, volume_id, session=None):
        for volume_info in reversed(self.db["volume_info"]):
            if volume_info["volume_id"] == volume_id:
                return self.FakeInfo(**volume_info)


    def volume_info_get_latest(self, volume_id, session=None):
        for volume_info in reversed(self.db["volume_info"]):
            if volume_info["volume_id"] == volume_id:
                return volume_info["id"]

    def volume_segment_end(self, volume_id, end_at, session=None):
        for segment in self.db["volume_segment"]:
            if not segment["end_at"]:
                segment["end_at"] = end_at


class TestCase(tests.TestCase):
    run_instance_body = {
        "_context_roles": [
            "projectmanager"
        ], 
        "_context_request_id": "29615116-ddd0-4a20-8018-ef5f90f8bdf3", 
        "args": {
            "request_spec": {
                "num_instances": 1, 
                "image": {
                    "status": "active", 
                    "deleted": False, 
                    "container_format": "ami", 
                    "updated_at": "2011-12-05 12:15:26.659439", 
                    "is_public": True, 
                    "deleted_at": None, 
                    "properties": {
                        "kernel_id": "2", 
                        "owner": None, 
                        "min_ram": "0", 
                        "ramdisk_id": "1", 
                        "min_disk": "0"
                    }, 
                    "size": 216858624, 
                    "name": "SL61", 
                    "checksum": "ecd1d23a8039b72812db4fee5a11a547", 
                    "created_at": "2011-12-05 12:15:25.541042", 
                    "disk_format": "ami", 
                    "id": 4, 
                    "location": "file:///var/lib/glance/images/4"
                }, 
                "filter": None, 
                "instance_type": {
                    "rxtx_quota": 0, 
                    "deleted": False, 
                    "updated_at": None, 
                    "extra_specs": {}, 
                    "flavorid": 2, 
                    "id": 5, 
                    "local_gb": 20, 
                    "deleted_at": None, 
                    "name": "m1.small", 
                    "created_at": None, 
                    "memory_mb": 2048, 
                    "vcpus": 1, 
                    "rxtx_cap": 0, 
                    "swap": 0
                }, 
                "blob": None, 
                "instance_properties": {
                    "vm_state": "building", 
                    "availability_zone": None, 
                    "ramdisk_id": "1", 
                    "instance_type_id": 5, 
                    "user_data": "", 
                    "vm_mode": None, 
                    "reservation_id": "r-851pambx", 
                    "root_device_name": None, 
                    "user_id": "admin", 
                    "display_description": None, 
                    "key_data": None, 
                    "power_state": 0, 
                    "project_id": "systenant", 
                    "metadata": {}, 
                    "access_ip_v6": None, 
                    "access_ip_v4": None, 
                    "kernel_id": "2", 
                    "key_name": None, 
                    "display_name": None, 
                    "config_drive_id": "", 
                    "local_gb": 20, 
                    "locked": False, 
                    "launch_time": "2011-12-06T19:12:57Z", 
                    "memory_mb": 2048, 
                    "vcpus": 1, 
                    "image_ref": 4, 
                    "architecture": None, 
                    "os_type": None, 
                    "config_drive": ""
                }
            }, 
            "requested_networks": None, 
            "availability_zone": None, 
            "instance_id": 16, 
            "admin_password": None, 
            "injected_files": None
        }, 
        "_context_auth_token": None, 
        "_context_user_id": "admin", 
        "_context_read_deleted": False, 
        "_context_strategy": "noauth", 
        "_context_is_admin": True, 
        "_context_project_id": "systenant", 
        "_context_timestamp": "2011-12-06T19:12:57.805503", 
        "method": "run_instance", 
        "_context_remote_address": "128.107.79.131"
    }

    anything_instance_body = {
        "args": {
            "instance_id": run_instance_body["args"]["instance_id"],
        }
    }

    day = 1

    final_db = {
        "instance_info": [
            {"memory_mb": 2048, "project_id": "systenant", "instance_id": 16,
                "vcpus": 1, "local_gb": 20, "id": 1},
            {"memory_mb": 2048, "project_id": "systenant", "instance_id": 16,
                "vcpus": 1, "local_gb": 20, "id": 2}
        ],
        "volume_info": [],
        "volume_segment": [],
        "instance_segment": [
            {"instance_info_id": 1, "begin_at": datetime.datetime(2011, 1, 2, 0, 0), 
                "segment_type": 0, "id": 1, "end_at": datetime.datetime(2011, 1, 3, 0, 0)},
            {"instance_info_id": 1, "begin_at": datetime.datetime(2011, 1, 3, 0, 0),
                "segment_type": 7, "id": 2, "end_at": datetime.datetime(2011, 1, 4, 0, 0)},
            {"instance_info_id": 1, "begin_at": datetime.datetime(2011, 1, 4, 0, 0),
                "segment_type": 0, "id": 3, "end_at": datetime.datetime(2011, 1, 5, 0, 0)},
            {"instance_info_id": 1, "begin_at": datetime.datetime(2011, 1, 5, 0, 0),
                "segment_type": 3, "id": 4, "end_at": datetime.datetime(2011, 1, 6, 0, 0)},
            {"instance_info_id": 1, "begin_at": datetime.datetime(2011, 1, 6, 0, 0),
                "segment_type": 0, "id": 5, "end_at": datetime.datetime(2011, 1, 7, 0, 0)},
            {"instance_info_id": 1, "begin_at": datetime.datetime(2011, 1, 7, 0, 0),
                "segment_type": 4, "id": 6, "end_at": datetime.datetime(2011, 1, 8, 0, 0)},
            {"instance_info_id": 1, "begin_at": datetime.datetime(2011, 1, 8, 0, 0),
                "segment_type": 0, "id": 7, "end_at": datetime.datetime(2011, 1, 9, 0, 0)},
            {"instance_info_id": 2, "begin_at": datetime.datetime(2011, 1, 10, 0, 0),
                "segment_type": 0, "id": 8, "end_at": datetime.datetime(2011, 1, 11, 0, 0)},
            {"instance_info_id": 2, "begin_at": datetime.datetime(2011, 1, 11, 0, 0),
                "segment_type": 7, "id": 9, "end_at": datetime.datetime(2011, 1, 12, 0, 0)},
            {"instance_info_id": 2, "begin_at": datetime.datetime(2011, 1, 12, 0, 0),
                "segment_type": 0, "id": 10, "end_at": None}
        ]
    }

    def get_event_datetime(self):
        self.day += 1
        return datetime.datetime(2011, 1, self.day)

    def test_process_event_on_instances(self):
        self.maxDiff = 5000
        fake_db_api = FakeDbApi()
        for func_name in ("instance_info_create",
                          "instance_segment_create",
                          "instance_info_get_latest",
                          "instance_segment_end"):
            self.stubs.Set(db_api, func_name, getattr(fake_db_api, func_name))

        listener = nova_billing.ampq_listener.Listener('compute.#', instance)
        self.stubs.Set(utils, "now", self.get_event_datetime)
        class StubMessage(object):
            def ack(self):
                pass
        stubMessage = StubMessage()
        listener._process_message(self.run_instance_body, stubMessage)
        for method in ("stop_instance", "start_instance",
                       "pause_instance", "unpause_instance",
                       "suspend_instance", "resume_instance",
                       "terminate_instance"):
            self.anything_instance_body["method"] = method
            listener._process_message(self.anything_instance_body, stubMessage)
        listener._process_message(self.run_instance_body, stubMessage)
        for method in ("stop_instance", "start_instance"):
            self.anything_instance_body["method"] = method
            listener._process_message(self.anything_instance_body, stubMessage)

        self.stubs.UnsetAll()
        self.assertEqual(fake_db_api.db, self.final_db)

    create_local_volume_body = {
        "method" : "create_local_volume",
        "args" : {
            "instance_id" : 16,
            "device": "/dev/vdc",
            "size": 100500,
            "volume_id" : 14
        }
    }

    resize_local_volume_body = {
        "method" : "resize_local_volume",
        "args" : {
            "volume_id": 14,
            "new_size": 200500,
        }
    }

    delete_local_volume_body = {
        "method" : "delete_local_volume",
        "args" : {
            "volume_id": 14
        }
    }

    local_volumes_final_db = {
        'volume_info': [
                {'project_id': 'systenant', 'allocated_bytes': 100500, 'id': 1, 'volume_id': 14},
                {'project_id': 'systenant', 'allocated_bytes': 200500, 'id': 2, 'volume_id': 14}
        ],
        'instance_info': [
                {'memory_mb': 2048, 'project_id': 'systenant', 'instance_id': 16, 'vcpus': 1, 'local_gb': 20, 'id': 1}
        ],
        'volume_segment': [
                {'begin_at': datetime.datetime(2011, 1, 3, 0, 0), 'segment_type': 0, 'info_id': 1, 'id': 1,
                            'end_at': datetime.datetime(2011, 1, 4, 0, 0)},
                {'begin_at': datetime.datetime(2011, 1, 4, 0, 0), 'segment_type': 2, 'info_id': 1, 'id': 2,
                 'end_at': datetime.datetime(2011, 1, 5, 0, 0)},
                {'begin_at': datetime.datetime(2011, 1, 5, 0, 0), 'segment_type': 0, 'info_id': 2, 'id': 3,
                 'end_at': datetime.datetime(2011, 1, 6, 0, 0)}], 'instance_segment': [
                {'instance_info_id': 1, 'begin_at': datetime.datetime(2011, 1, 2, 0, 0), 'segment_type': 0, 'id': 1,
                 'end_at': None}
        ]
    }

    def test_process_event_on_local_volumes(self):
        self.maxDiff = 5000
        fake_db_api = FakeDbApi()
        for func_name in ("volume_info_create",
                          "volume_segment_create",
                          "volume_info_get_latest",
                          "volume_info_get",
                          "volume_segment_end",
                          "instance_info_create",
                          "instance_segment_create",
                          "instance_info_get_latest",
                          "instance_segment_end",
                          "instance_info_get"):
            self.stubs.Set(db_api, func_name, getattr(fake_db_api, func_name))
        self.stubs.Set(novaclient, "get_nova_client", lambda: None)
        listener = nova_billing.ampq_listener.Listener('compute.#', instance, local_volume)
        self.stubs.Set(utils, "now", self.get_event_datetime)
        class StubMessage(object):
            def ack(self):
                pass
        stubMessage = StubMessage()
        listener._process_message(self.run_instance_body, stubMessage)
        listener._process_message(self.create_local_volume_body, stubMessage)
        listener._process_message(self.resize_local_volume_body, stubMessage)
        listener._process_message(self.delete_local_volume_body, stubMessage)
        self.stubs.UnsetAll()
        self.assertEqual(fake_db_api.db, self.local_volumes_final_db)
