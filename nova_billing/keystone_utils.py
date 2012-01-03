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
Module for communication with Keystone.
"""

import ConfigParser

from novaclient import client as nova_client
from novaclient.keystone import tenants
from novaclient.keystone import users

from nova import flags
from nova import service


FLAGS = flags.FLAGS


_keystone_admin_token = None
_keystone_admin_url = None


def _get_keystone_stuff():
    config = ConfigParser.RawConfigParser()
    config.read("/etc/nova/%s" % FLAGS.api_paste_config)
    global _keystone_admin_token, _keystone_admin_url
    _keystone_admin_token = config.get("filter:authtoken", "admin_token")
    _keystone_admin_url = "%s://%s:%s/v2.0" % (
        config.get("filter:authtoken", "auth_protocol"),
        config.get("filter:authtoken", "auth_host"),
        config.get("filter:authtoken", "auth_port"))


def get_keystone_admin_token():
    if not _keystone_admin_token:
        _get_keystone_stuff()
    return _keystone_admin_token


def get_keystone_admin_url():
    if not _keystone_admin_url:
        _get_keystone_stuff()
    return _keystone_admin_url


class KeystoneClient(object):
    def __init__(self, client):
        self.client = client
        self.tenants = tenants.TenantManager(self)
        self.users = users.UserManager(self)

    def authenticate(self):
        pass


class KeystoneTenants(object):
    tenants = []

    def __init__(self):
        keystone_admin_url = get_keystone_admin_url()
        conn = nova_client.HTTPClient("admin", "secrete", "systenant", keystone_admin_url)
        conn.auth_token = get_keystone_admin_token()
        conn.management_url = keystone_admin_url
        self.keystone_client = KeystoneClient(conn)

    def get_tenants(self):
        self.tenants = self.keystone_client.tenants.list()
        return self.tenants
