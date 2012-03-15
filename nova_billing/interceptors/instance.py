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
__author__ = 'bfilippov'

from nova_billing.segment import InstanceSegment
from nova_billing.utils import bill
from nova_billing import vm_states
from nova_billing.db import api as db_api
from nova import log as logging

__LOG = logging.getLogger("nova_billing.interceptors.instance")


@bill(InstanceSegment())
def run_instance(body, message):
    instance_info = {
        "project_id": body["args"]["request_spec"]
            ["instance_properties"]["project_id"],
        "instance_id": body["args"]["instance_id"],
    }
    instance_type = body["args"]["request_spec"]["instance_type"]
    for key in "local_gb", "memory_mb", "vcpus":
        instance_info[key] = instance_type[key]
    instance_info_ref = db_api.instance_info_create(instance_info)

    return {
        "instance_info_id": instance_info_ref.id,
        "segment_type": vm_states.ACTIVE,
    }

@bill(InstanceSegment())
def start_instance(body, message):
    return {
        "segment_type": vm_states.ACTIVE,
    }

@bill(InstanceSegment())
def stop_instance(body, message):
    return {
        "segment_type": vm_states.STOPPED,
    }

@bill(InstanceSegment())
def unpause_instance(body, message):
    return {
        "segment_type": vm_states.ACTIVE,
    }

@bill(InstanceSegment())
def pause_instance(body, message):
    return {
        "segment_type": vm_states.PAUSED,
    }

@bill(InstanceSegment())
def resume_instance(body, message):
    return {
        "segment_type": vm_states.ACTIVE,
    }

@bill(InstanceSegment())
def suspend_instance(body, message):
    return {
        "segment_type": vm_states.SUSPENDED
    }

@bill(InstanceSegment())
def terminate_instance(body, message):
    return None