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
Tests for nova_billing.rest
"""

import os
import sys
import json
import datetime
import unittest
import stubout

import routes
import webob

from nova_billing import rest
from nova_billing import utils
from nova_billing import nova_utils
from nova_billing import keystone_utils
from nova_billing import glance_utils
from nova_billing.db import api as db_api

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tests


class FakeDbApi(object):
    @staticmethod
    def volumes_on_interval(period_start, period_stop, project_id = None):
        total_statistics = {
            "1": {
                12: {
                    "created_at": datetime.datetime(2011, 1, 1),
                    "destroyed_at": datetime.datetime(2011, 1, 2),
                    "usage": {"allocated_bytes": 3600 * 12},
                },
                14: {
                    "created_at": datetime.datetime(2011, 1, 4),
                    "destroyed_at": datetime.datetime(2011, 2, 1),
                    "usage": {"allocated_bytes": 3600 * 67},
                },
            },
            "12": {
                54: {
                    "created_at": datetime.datetime(2011, 1, 1),
                    "destroyed_at": datetime.datetime(2011, 1, 2),
                    "usage": {"allocated_bytes": 3600 * 73},
                },
                67: {
                    "created_at": datetime.datetime(2011, 2, 1),
                    "destroyed_at": datetime.datetime(2011, 2, 3),
                    "usage": {"allocated_bytes": 3600 * 57},
                },
                90: {
                    "created_at": datetime.datetime(2013, 3, 4),
                    "destroyed_at": datetime.datetime(2013, 5, 6),
                    "usage": {"allocated_bytes": 3600 * 20},
                },
            }
        }
        if project_id:
            total_statistics = {project_id: total_statistics[project_id]}
        for project in total_statistics:
            total_statistics[project] = dict(
                [(key, value)
                 for key, value in total_statistics[project].items()
                 if (value["created_at"] <= period_stop and
                    value["destroyed_at"] >= period_start)
                ])
        return total_statistics

    @staticmethod
    def instances_on_interval(period_start, period_stop, project_id=None):
        total_statistics = {
            "1": {
                12: {
                    "created_at": datetime.datetime(2011, 1, 1),
                    "destroyed_at": datetime.datetime(2011, 1, 2),
                    "usage": {"local_gb": 3600 * 12, "memory_mb": 3600 * 45, "vcpus": 3600 * 39},
                },
                14: {
                    "created_at": datetime.datetime(2011, 1, 4),
                    "destroyed_at": datetime.datetime(2011, 2, 1),
                    "usage": {"local_gb": 3600 * 67, "memory_mb": 3600 * 10, "vcpus": 3600 * 41},
                },
            },
            "12": {
                54: {
                    "created_at": datetime.datetime(2011, 1, 1),
                    "destroyed_at": datetime.datetime(2011, 1, 2),
                    "usage": {"local_gb": 3600 * 73, "memory_mb": 3600 * 66, "vcpus": 3600 * 39},
                },
                67: {
                    "created_at": datetime.datetime(2011, 2, 1),
                    "destroyed_at": datetime.datetime(2011, 2, 3),
                    "usage": {"local_gb": 3600 * 57, "memory_mb": 3600 * 99, "vcpus": 3600 * 03},
                },
                90: {
                    "created_at": datetime.datetime(2013, 3, 4),
                    "destroyed_at": datetime.datetime(2013, 5, 6),
                    "usage": {"local_gb": 3600 * 20, "memory_mb": 3600 * 51, "vcpus": 3600 * 43},
                },
            }
        }
        if project_id:
            total_statistics = {project_id: total_statistics[project_id]}
        for project in total_statistics:
            total_statistics[project] = dict(
                [(key, value)
                 for key, value in total_statistics[project].items()
                 if (value["created_at"] <= period_stop and
                    value["destroyed_at"] >= period_start)
                ])
        return total_statistics

class FakeGlanceApi(object):
    @staticmethod
    def images_on_interval(period_start, period_stop, tenant_by_id, auth_tok, tenant_id=None):
        total_statistics = {
            "1": {
                21: {
                    "created_at": datetime.datetime(2011, 1, 1),
                    "destroyed_at": datetime.datetime(2011, 1, 2),
                    "name": "RHEL 6.1",
                    "usage": {"local_gb": 3600 * 12},
                },
                39: {
                    "created_at": datetime.datetime(2011, 1, 4),
                    "destroyed_at": datetime.datetime(2011, 2, 1),
                    "name": "Ubuntu kernel",
                    "usage": {"local_gb": 3600 * 67},
                },
            },
            "12": {
                94: {
                    "created_at": datetime.datetime(2011, 1, 1),
                    "destroyed_at": datetime.datetime(2011, 1, 2),
                    "name": "Gentoo initrd",
                    "usage": {"local_gb": 3600 * 73},
                }
            }
        }
        if tenant_id:
            project_id = tenant_by_id[tenant_id]
            total_statistics = {project_id: total_statistics[project_id]}
        for proj in total_statistics:
            total_statistics[proj] = dict(
                [(key, value)
                 for key, value in total_statistics[proj].items()
                 if (value["created_at"] <= period_stop and
                    value["destroyed_at"] >= period_start)
                ])
        return total_statistics

class TestCase(tests.TestCase):
    def test_billing_application(self):
        """
        Test different billing REST API queries.
        """
        fake_db_api = FakeDbApi()
        fake_glance_api = FakeGlanceApi()
        for func_name in ("instances_on_interval", "volumes_on_interval"):
            self.stubs.Set(db_api, func_name, getattr(fake_db_api, func_name))
        for func_name in ("images_on_interval", ):
            self.stubs.Set(glance_utils, func_name, getattr(fake_glance_api, func_name))

        self.stubs.Set(utils, "now", lambda: datetime.datetime(2011, 1, 1))
        from keystoneclient.v2_0.tenants import Tenant
        self.stubs.Set(keystone_utils.KeystoneTenants, "get_tenants",
                       lambda self, token: [Tenant(None, {"id": "1", "name": "systenant"}),
                                            Tenant(None, {"id": "12", "name": "tenant12"})])

        def json_load_from_file(filename):
            json_file = open(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), filename),
                "rt")
            json_obj = json.load(json_file)
            json_file.close()
            return json_obj

        for request, result_body in json_load_from_file("api-requests.json").items():
            result = webob.Request.blank(
                    request,
                    headers={"X_ROLE": "Admin",
                             "X_TENANT_ID": "1"}).\
                    get_response(rest.BillingApplication())
            self.assertEqual(result.status_int, 200)
            self.assertEqual(json.loads(result.body), result_body)

        for request in json_load_from_file("status-requests.json"):
            result = webob.Request.blank(
                    request["request"],
                    headers=request["headers"],).\
                    get_response(rest.BillingApplication())
            self.assertEqual(
                    result.status_int, request["status_int"],
                    "Expected %s but got %s for %s" %
                    (request["status_int"], result.status_int, request["request"]))
