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

from nova_billing import utils

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
    vm_states.ACTIVE: ("memory_mb", "vcpus"),
    vm_states.SUSPENDED: ("memory_mb"),
    vm_states.PAUSED: ("memory_mb"),
    vm_states.STOPPED: ( ),
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


nova_client = utils.get_nova_client()

# Cache flavors here
flavors = {}
no_flavor = {
    "name": "<none>",
    "local_gb": 0,
    "memory_mb": 0,
    "vcpus": 0,
} 

def get_flavor(flavor_id):
    try:
        return flavors[flavor_id]
    except KeyError:
        pass
    try:
        flav = nova_client.flavors.get(flavor_id)
    except:
        return no_flavor
    flav = {
        "name": flav.name,
        "local_gb": flav.disk,
        "memory_mb": flav.ram,
        "vcpus": flav.vcpus,
    }
    flavors[flavor_id] = flav
    return flav


def get_instance_flavor(instance_id):
    try:
        return get_flavor(
            nova_client.servers.get(instance_id).flavor["id"])
    except:
        return no_flavor


def create_heart_request(method, body):
    try:
        state = target_state[method]
    except KeyError:
        return None

    heart_request = {
        "type": "nova/instance",
        "name": body["args"]["instance_id"],
    }
    child_keys = ("local_gb", "memory_mb", "vcpus")
    if method == "run_instance":
        heart_request["fixed"] = 0
        instance_type = body["args"]["request_spec"]["instance_type"] 
        heart_request["attrs"] = { "instance_type": instance_type["name"] }
        heart_request["children"] = [
            {"type": key, "linear": instance_type[key]}
            for key in child_keys]
    elif method == "terminate_instance":
        heart_request["fixed"] = None
        heart_request["children"] = [
            {"type": key, "fixed": None}
            for key in child_keys]
    else:
        used = used_resources[state]
        flav = get_instance_flavor(body["args"]["instance_id"])
        heart_request["children"] = [
            {"type": key,
             "linear": flav[key] if key in used else 0}
            for key in ("memory_mb", "vcpus")]
    return heart_request
