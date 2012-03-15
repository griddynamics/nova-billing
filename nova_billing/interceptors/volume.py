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
from nova_billing.novaclient import get_nova_client
from nova_billing import volume_states, vm_states
from nova_billing.db import api as db_api
from nova_billing.utils import bill
from nova_billing.segment import VolumeSegment, InstanceSegment
from nova import log as logging

__author__ = 'bfilippov'

__LOG = logging.getLogger('nova_billing.interceptors.volume')

@bill(VolumeSegment())
def create_local_volume(body, message):
    instance_id = body['args']['instance_id']
    instance_info = db_api.instance_info_get(instance_id)
    if not instance_info:
        __bill_single_instance_from_api(body, message)
        instance_info = db_api.instance_info_get(instance_id)

    volume_info = db_api.volume_info_create({
        'volume_id': body['args']['volume_id'],
        'project_id': instance_info.project_id,
        'allocated_bytes': body['args']['size'],
    })
    return {
        "info_id": volume_info.id,
        "segment_type": volume_states.VOLUME_ATTACHED,
    }

@bill(VolumeSegment())
def delete_local_volume(body, message):
    return None

@bill(VolumeSegment())
def resize_local_volume(body, message):
    __pre_resize_local_volume(body, message)
    old_volume_info = db_api.volume_info_get(body['args']['volume_id'])
    project_id = old_volume_info.project_id
    volume_info = db_api.volume_info_create({
        'volume_id': body['args']['volume_id'],
        'project_id': project_id,
        'allocated_bytes': body['args']['new_size']
    })
    return {
        "info_id": volume_info.id,
        "segment_type": volume_states.VOLUME_ATTACHED,
    }

@bill(VolumeSegment())
def __pre_resize_local_volume(body, message):
    return {
        'segment_type': volume_states.VOLUME_DELETED
    }

@bill(InstanceSegment())
def __bill_single_instance_from_api(body, message):
    instance_info = get_nova_client().get_instance_info(body['args']['instance_id'])
    instance_info_ref = db_api.instance_info_create(instance_info)
    return {
        "instance_info_id": instance_info_ref.id,
        "segment_type": vm_states.ACTIVE
    }

