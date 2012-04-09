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


class vm_states(object):
    ACTIVE = 0
    BUILDING = 1
    REBUILDING = 2
    
    PAUSED = 3
    SUSPENDED = 4
    RESCUED = 5
    DELETED = 6
    STOPPED = 7
    
    MIGRATING = 8
    RESIZING = 9
    
    ERROR = 10


used_resources = {
    vm_states.ACTIVE: ("local_gb", "memory_mb", "vcpus"),
    vm_states.SUSPENDED: ("local_gb", "memory_mb"),
    vm_states.PAUSED: ("local_gb", "memory_mb"),
    vm_states.STOPPED: ("local_gb", ),
}


target_state = {
    "run_instance": vm_states.ACTIVE,
    "terminate_instance": vm_states.DELETED,
    "start_instance": vm_states.ACTIVE,
    "stop_instance": vm_states.STOPPED,
    "unpause_instance": vm_states.ACTIVE,
    "pause_instance": vm_states.PAUSED,
    "resume_instance": vm_states.ACTIVE,
    "suspend_instance": vm_states.SUSPENDED,
}

def create_heart_request(method, body):
    try:
        state = target_state[method]
    except KeyError:
        return None

    heart_request = {
        "type": "nova/instance",
        "name": body["args"]["instance_id"],
        "account": body["_context_project_id"],        
    }
    if method == "run_instance":
        instance_type = body["args"]["request_spec"]["instance_type"] 
        heart_request["attrs"] = { "instance_type": instance_type["name"] }
        children = []
        for key in "local_gb", "memory_mb", "vcpus":
            children.append({"type": key, 
                             # TODO: multiply on the tariff
                             "cost": instance_type[key]})
        heart_request["children"] = children
    return heart_request
