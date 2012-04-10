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


target_methods = (
    "create_local_volume",
    "delete_local_volume",
    "resize_local_volume",
)


def create_heart_request(method, body):
    if method not in target_methods:
        return None
    
    heart_request = {
        "type": "nova/volume",
        "name": body["args"]["volume_id"],       
    }

    # TODO: multiply cost on the tariff
    if method == "create_local_volume":        
        heart_request["cost"] = body["args"]["size"]
    elif method == "resize_local_volume":
        heart_request["cost"] = body["args"]["new_size"]                        
    return heart_request
