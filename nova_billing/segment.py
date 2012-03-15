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

from nova_billing.db import api

class Segment(object):
    def end(self, body, time):
        raise NotImplementedError('This must be implemented in subclass')

    def start(self, body, segment_info, time):
        raise NotImplementedError('This must be implemented in subclass')


class VolumeSegment(Segment):
    def end(self, body, time):
        api.volume_segment_end(body["args"]["volume_id"], time)

    def start(self, body, segment_info, time):
        segment_info["begin_at"] = time
        if not segment_info.has_key("info_id"):
            segment_info["info_id"] = \
                api.volume_info_get_latest(body["args"]["volume_id"])
        api.volume_segment_create(segment_info)


class InstanceSegment(Segment):
    def end(self, body, time):
        api.instance_segment_end(body["args"]["instance_id"], time)

    def start(self, body, segment_info, time):
        segment_info['begin_at'] = time
        if not segment_info.has_key('instance_info_id'):
            segment_info['instance_info_id'] = \
                api.instance_info_get_latest(body['args']['instance_id'])
        api.instance_segment_create(segment_info)