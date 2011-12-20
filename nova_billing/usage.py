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
