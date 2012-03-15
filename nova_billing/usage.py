from nova_billing import vm_states, volume_states
from nova_billing.utils import total_seconds

__author__ = 'bfilippov'

def update_instance_usage(usage, begin_at, end_at, type, info):
    """
    Increment used resource statistics depending on ``vm_state``.
    Statistics is measured in (resource unit * second).
    """
    used_resources = {
        vm_states.ACTIVE: ("local_gb", "memory_mb", "vcpus"),
        vm_states.SUSPENDED: ("local_gb", "memory_mb"),
        vm_states.PAUSED: ("local_gb", "memory_mb"),
        vm_states.STOPPED: ("local_gb", ),
    }

    length = total_seconds(end_at - begin_at)
    for key in ("local_gb", "memory_mb", "vcpus"):
        usage[key] = (usage.get(key, 0) +
                      (length * info[key]
                       if key in used_resources.get(type, [])
                       else 0))

def update_volume_usage(usage, begin_at, end_at, type, info):
    """
    Increment used resource statistics depending on ``volume_state``.
    Statistics is measured in (resource unit * second).
    """
    if type == volume_states.VOLUME_ATTACHED:
        key = "allocated_bytes"
        length = total_seconds(end_at - begin_at)
        usage[key] = (usage.get(key, 0) +
                  length * info[key])
