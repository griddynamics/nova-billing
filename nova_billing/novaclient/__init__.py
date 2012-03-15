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

import ConfigParser
from collections import namedtuple
from nova import flags
from nova_billing.novaclient.client import NovaApiClient

FLAGS = flags.FLAGS
Options = namedtuple('Options', 'auth_url token use_keystone debug')

def get_nova_client():
    config = ConfigParser.RawConfigParser(defaults={
        'admin_token': None,
        'auth_uri': None,
        'use_keystone': None,
        'debug': None,
        'user': None,
        'password': None
    })

    config.read(FLAGS.billing_api_paste_config)

    admin_token = config.get('filter:authtoken', 'admin_token')
    auth_uri = config.get('filter:authtoken', 'auth_uri')
    use_keystone = config.get('filter:authtoken', 'use_keystone')
    debug = config.get('filter:authtoken', 'debug')
    user=config.get('filter:authtoken', 'user')
    password=config.get('filter:authtoken', 'password')
    class Options(object):
        def __init__(self, **entries):
            self.__dict__.update(entries)

        def __getattr__(self, item):
            return self.__dict__.get(item, None)

    options = Options(token=admin_token, auth_url=auth_uri, use_keystone=use_keystone,
        debug=debug, username=user, password=password)

    return NovaApi(NovaApiClient(options))


class NovaApi(object):

    def __init__(self, nova_api_client):
        self.client = nova_api_client

    def get_server(self, id):
        return self.client.get("/servers/{0}".format(id)).get("server", None)

    def get_flavor(self, id):
        return self.client.get("/flavors/{0}".format(id)).get("flavor", None)

    def list_flavors(self):
        return self.client.get("/flavors", None)

    def get_instance_info(self, id):
        """
        Get Instance Info
        """
        server = self.get_server(id)
        if not server:
            raise RuntimeError("No such server %s found" % id)
        server = server
        instance_info = {
            "project_id": server["tenant_id"],
            "instance_id": id,
        }
        flavor = self.get_flavor(server["flavor"]["id"])
        instance_info["local_gb"] = flavor["disk"]
        instance_info["memory_mb"] =flavor["ram"]
        instance_info["vcpus"] = flavor["vcpus"]

        return instance_info
