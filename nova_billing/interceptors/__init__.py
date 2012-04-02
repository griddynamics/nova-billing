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
import instance
import volume

def make_interceptor(*methods):
    interceptor = {}
    for method in methods:
        interceptor[method.__name__] = method
    return interceptor

instance = make_interceptor(instance.run_instance, instance.start_instance,
                            instance.pause_instance, instance.resume_instance,
                            instance.stop_instance, instance.suspend_instance,
                            instance.terminate_instance, instance.unpause_instance)

local_volume = make_interceptor(volume.create_local_volume, volume.delete_local_volume,
                                volume.resize_local_volume)