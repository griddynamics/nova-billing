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
Usage calculations for different VM states.
"""

from nova_billing import vm_states


def total_seconds(td):
    """This function is added for portability 
    because timedelta.total_seconds() 
    was introduced only in python 2.7."""
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6


used_resources = {
    vm_states.ACTIVE: ("local_gb", "memory_mb", "vcpus"),
    vm_states.SUSPENDED: ("local_gb", "memory_mb"),
    vm_states.PAUSED: ("local_gb", "memory_mb"),
    vm_states.STOPPED: ("local_gb", ),
}


def usage_add(usage, begin_at, end_at, vm_state, instance_info):
    """
    Increment used resource statistics depending on ``vm_state``.
    Statistics is measured in (resource unit * second).
    """
    length = total_seconds(end_at - begin_at)
    for key in ("local_gb", "memory_mb", "vcpus"):
        usage[key] = (usage.get(key, 0) +
            (length * instance_info[key]
             if key in used_resources.get(vm_state, [])
             else 0))


def dict_add(a, b):
    """
    Increment all keys in ``a`` on keys in ``b``.
    """
    for key in b:
        a[key] = a.get(key, 0) + b[key]
