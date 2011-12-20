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
Possible vm states for instances.

There are integers for string states from ``nova.compute.vm_states``.

The following states are stored in the database:

* ACTIVE
* PAUSED
* SUSPENDED
* STOPPED
"""

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
