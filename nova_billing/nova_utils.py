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

"""
Module for communication with Nova.
"""

from nova.auth import manager
from nova import flags


FLAGS = flags.FLAGS


class NovaProjects(object):
    projects = []

    def __init__(self):
        self.manager = manager.AuthManager()

    def get_projects(self):
        self.projects = []
        for project in self.manager.get_projects(None):
            self.projects.append(project.name)
        return self.projects

