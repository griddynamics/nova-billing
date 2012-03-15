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
import httplib
import json
import os

import logging

from urlparse import urlparse
from nova import flags

FLAGS = flags.FLAGS
LOG = logging.getLogger("nova_billing.nova.client")




class CommandError(RuntimeError):
    def __init__(self, status, message):
        RuntimeError.__init__(self, message, status)

    def status(self):
        return self.args[1]

    def message(self):
        return self.args[0]


class EndpointNotFound(Exception):
    """Could not find Service or Region in Service Catalog."""
    pass


class TokenInfo(object):
    """Helper methods for dealing with a Keystone Token Info."""

    def __init__(self, resource_dict):
        self.token_info = resource_dict
        self.roles = None

    def get_token(self):
        return self.token_info['access']['token']['id']

    def get_roles(self):
        if self.roles is None:
            try:
                self.roles = set([role_ref["name"]
                    for role_ref in
                        self.token_info["access"]["user"]["roles"]])
            except KeyError:
                self.roles = set()
        return self.roles

    def url_for(self, attr=None, filter_value=None,
                    service_type='compute', endpoint_type='publicURL'):
        """Fetch the public URL from the Compute service for
        a particular endpoint attribute. If none given, return
        the first. See tests for sample service catalog."""
        if 'endpoints' in self.token_info:
            # We have a bastardized service catalog. Treat it special. :/
            for endpoint in self.token_info['endpoints']:
                if not filter_value or endpoint[attr] == filter_value:
                    return endpoint[endpoint_type]
            raise EndpointNotFound()

        # We don't always get a service catalog back ...
        if not 'serviceCatalog' in self.token_info['access']:
            raise EndpointNotFound()

        # Full catalog ...
        catalog = self.token_info['access']['serviceCatalog']

        for service in catalog:
            if service['type'] != service_type:
                continue

            endpoints = service['endpoints']
            for endpoint in endpoints:
                if not filter_value or endpoint[attr] == filter_value:
                    return endpoint[endpoint_type]

        raise EndpointNotFound()


class NovaApiClient(object):
    DEFAULTS = {
        "use_keystone": True,
        "auth_url": os.environ.get("OS_AUTH_URL", os.environ.get("NOVA_URL")),
        "token": os.environ.get("OS_TOKEN"),
        "debug": os.environ.get("NOVA2OOLS_DEBUG", "") not in ["", "0", "f", "false", "no", "off"],
    }

    def __init__(self, options, service_type="compute"):
        self.options = options
        self.service_type = service_type
        self.token_info = None
        self.auth()

    def auth(self):
        if self.options.token:
            self.__token = self.options.token
        self.__management_url = self.options.endpoint
        if not (self.options.token and self.options.endpoint):
            if not self.options.auth_url:
                raise CommandError(1, "Authentication URL is required")

            if self.options.use_keystone is None:
                raise CommandError(1, "You should select auth type (use_keystone parameter)")
            if self.options.use_keystone:
                self.auth_keystone()
            else:
                self.auth_nova()
        else:
            self.__auth_headers = {
                "X-Auth-Token": self.__token,
            }

    def auth_nova(self):
        auth_headers = {
            "X-Auth-User": self.options.username,
            "X-Auth-Key": self.options.password,
            "X-Auth-Project-Id": self.options.tenant_name
        }
        resp, _ = self.request(self.options.auth_url, "GET", headers=auth_headers)
        self.__token = resp.getheader("X-Auth-Token")
        if not self.__management_url:
            self.__management_url = resp.getheader("X-Server-Management-Url")
        self.__auth_headers = {
            "X-Auth-Project-Id": self.options.tenant_name,
            "X-Auth-Token": self.__token
        }

    def auth_keystone(self):
        token = self.options.token
        password = self.options.password
        username = self.options.username
        tenant_id = self.options.tenant_id
        tenant_name = self.options.tenant_name
        if token:
            params = {"auth": {"token": {"id": token}}}
        elif username and password:
            params = {"auth": {"passwordCredentials": {"username": username,
                                                       "password": password}}}
        else:
            raise CommandError(1, "A username and password or token is required")

        if tenant_id:
            params['auth']['tenantId'] = tenant_id
        elif tenant_name:
            params['auth']['tenantName'] = tenant_name
        _, access = self.request(
                self.options.auth_url + "/tokens",
                "POST",
                body=params,
                headers={"Content-Type": "application/json"})
        if access is None:
            raise CommandError(1, "You are not authenticated")
        self.token_info = TokenInfo(access)

        if not self.__management_url and self.service_type:
            self.set_service_type(self.service_type)

        self.__auth_headers = {
            "X-Auth-Token": self.token_info.get_token()
        }
        if not tenant_id:
            tenant_id = access['access']['token']['tenant']['id']
            self.options.tenant_id = tenant_id
        self.__auth_headers["X-Tenant"] = tenant_id
        if tenant_name:
            self.__auth_headers["X-Tenant-Name"] = tenant_name

    @property
    def auth_token(self):
        return self.__auth_headers["X-Auth-Token"]

    @property
    def tenant_id(self):
        return self.options.tenant_id

    @property
    def username(self):
        return self.options.username

    def set_service_type(self, service_type, endpoint_type='publicURL'):
        self.__management_url = self.url_for(
                    service_type=service_type, endpoint_type=endpoint_type)
        self.service_type = service_type

    def url_for(self, service_type, endpoint_type='publicURL'):
        try:
            return self.token_info.url_for(
            service_type=service_type, endpoint_type=endpoint_type)
        except EndpointNotFound:
            raise CommandError(1, "Could not find `%s' in service catalog" % service_type)

    def http_log(self, args, kwargs, resp, body):
        if not self.options.debug:
            return

        string_parts = ["curl -i '%s' -X %s" % args]

        for element in kwargs['headers']:
            header = ' -H "%s: %s"' % (element, kwargs['headers'][element])
            string_parts.append(header)

        print "REQ: %s\n" % "".join(string_parts)
        if 'body' in kwargs:
            print "REQ BODY: %s\n" % (kwargs['body'])
        if resp:
            print "RESP: %s\nRESP BODY: %s\n" % (resp.status, body)

    def request(self, *args, **kwargs):
        kwargs.setdefault('headers', kwargs.get('headers', {}))
        if 'body' in kwargs and kwargs['body'] is not None:
            kwargs['headers']['Content-Type'] = 'application/json'
            kwargs['body'] = json.dumps(kwargs['body'])

        resp, body = None, None
        try:
            parsed = urlparse(args[0])
            client = httplib.HTTPConnection(parsed.netloc)
            request_uri = ("?".join([parsed.path, parsed.query])
                           if parsed.query
                           else parsed.path)
            client.request(args[1], request_uri, **kwargs)
            resp = client.getresponse()
            body = resp.read()
        finally:
            self.http_log(args, kwargs, resp, body)
        return (resp, self.__validate_response(resp, body))

    def get(self, path):
        return self.request(self.__management_url + path, "GET", headers=self.__auth_headers)[1]

    def post(self, path, body):
        return self.request(self.__management_url + path, "POST", body=body, headers=self.__auth_headers)[1]

    def action(self, path):
        return self.request(self.__management_url + path, "POST", headers=self.__auth_headers)[1]

    def put(self, path, body):
        return self.request(self.__management_url + path, "PUT", body=body, headers=self.__auth_headers)[1]

    def delete(self, path):
        return self.request(self.__management_url + path, "DELETE", headers=self.__auth_headers)[1]

    def __validate_response(self, response, response_content):
        if response.status == 200:
            json_response = json.loads(response_content)
            return json_response
        if response.status == 404:
            raise CommandError(1, response.reason)
        if response.status == 401:
            raise CommandError(1, response.reason)
        if response.status == 204: # No Content
            return None
        if response.status == 202: # Accepted
            try:
                json_response = json.loads(response_content)
            except ValueError:
                return response_content
            return json_response
        if response.status == 400: # Bad Request
            json_response = json.loads(response_content)
            raise CommandError(1, "Bad Request: {0}".format(json_response["badRequest"]["message"]))
        raise CommandError(1, "Unhandled response code: %s (%s)" % (response.status, response.reason))
