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


import json
import datetime
import unittest
import stubout

import routes
import webob

from nova_billing import rest
from nova_billing.db import api as db_api


class FakeDbApi(object):
    @staticmethod
    def instances_on_interval(period_start, period_stop, project_id=None):
        total_statistics = {
            "systenant": {
                12: {
                    "created_at": datetime.datetime(2011, 1, 1),
                    "destroyed_at": datetime.datetime(2011, 1, 2),
                    "running": 3600 * 1,
                    "usage": {"local_gb": 3600 * 12, "memory_mb": 3600 * 45, "vcpus": 3600 * 39},
                },
                14: {
                    "created_at": datetime.datetime(2011, 1, 4),
                    "destroyed_at": datetime.datetime(2011, 2, 1),
                    "running": 3600 * 13,
                    "usage": {"local_gb": 3600 * 67, "memory_mb": 3600 * 10, "vcpus": 3600 * 41},
                },
            },
            "tenant12": {
                54: {
                    "created_at": datetime.datetime(2011, 1, 1),
                    "destroyed_at": datetime.datetime(2011, 1, 2),
                    "running": 3600 * 111,
                    "usage": {"local_gb": 3600 * 73, "memory_mb": 3600 * 66, "vcpus": 3600 * 39},
                },
                67: {
                    "created_at": datetime.datetime(2011, 2, 1),
                    "destroyed_at": datetime.datetime(2011, 2, 3),
                    "running": 3600 * 513,
                    "usage": {"local_gb": 3600 * 57, "memory_mb": 3600 * 99, "vcpus": 3600 * 03},
                },
                90: {
                    "created_at": datetime.datetime(2013, 3, 4),
                    "destroyed_at": datetime.datetime(2013, 5, 6),
                    "running": 3600 * 1013,
                    "usage": {"local_gb": 3600 * 20, "memory_mb": 3600 * 51, "vcpus": 3600 * 43},
                },
            }
        }
        if project_id:
            total_statistics = {project_id: total_statistics[project_id]}
        for proj in total_statistics:
            total_statistics[proj] = dict(
                [(key, value)
                 for key, value in total_statistics[proj].items()
                 if (value["created_at"] <= period_stop and
                    value["destroyed_at"] >= period_start)
                ])
        return total_statistics


class TestCase(unittest.TestCase):
    def setUp(self):
        """Run before each test method to initialize test environment."""
        super(TestCase, self).setUp()
        self.stubs = stubout.StubOutForTesting()

    def test_billing_application(self):
        """
        Test different billing REST API queries.
        """
        rest_calls = {
            "/projects-all/2011/1/1": {
                "period_start": "2011-01-01T00:00:00Z",
                "projects": {
                    "tenant12": {
                        "url": "http://localhost:80/projects/tenant12",
                        "usage": {
                            "memory_mb": 66.0,
                            "vcpus": 39.0,
                            "local_gb": 73.0
                        },
                        "running": 111.0,
                        "instances_count": 1,
                        "name": "tenant12"
                    },
                    "systenant": {
                        "url": "http://localhost:80/projects/systenant",
                        "usage": {
                            "memory_mb": 45.0,
                            "vcpus": 39.0,
                            "local_gb": 12.0
                        },
                        "running": 1.0,
                        "instances_count": 1,
                        "name": "systenant"
                    }
                },
                "period_end": "2011-01-02T00:00:00Z"
            },
            "/projects-all/2011/01": {
                "period_start": "2011-01-01T00:00:00Z",
                "projects": {
                    "tenant12": {
                        "url": "http://localhost:80/projects/tenant12",
                        "usage": {
                            "memory_mb": 165.0,
                            "vcpus": 42.0,
                            "local_gb": 130.0
                        },
                        "running": 624.0,
                        "instances_count": 2,
                        "name": "tenant12"
                    },
                    "systenant": {
                        "url": "http://localhost:80/projects/systenant",
                        "usage": {
                            "memory_mb": 55.0,
                            "vcpus": 80.0,
                            "local_gb": 79.0
                        },
                        "running": 14.0,
                        "instances_count": 2,
                        "name": "systenant"
                    }
                },
                "period_end": "2011-02-01T00:00:00Z"
            },
            "/projects-all/2011": {
                "period_start": "2011-01-01T00:00:00Z",
                "projects": {
                    "tenant12": {
                        "url": "http://localhost:80/projects/tenant12",
                        "usage": {
                            "memory_mb": 165.0,
                            "vcpus": 42.0,
                            "local_gb": 130.0
                        },
                        "running": 624.0,
                        "instances_count": 2,
                        "name": "tenant12"
                    },
                    "systenant": {
                        "url": "http://localhost:80/projects/systenant",
                        "usage": {
                            "memory_mb": 55.0,
                            "vcpus": 80.0,
                            "local_gb": 79.0
                        },
                        "running": 14.0,
                        "instances_count": 2,
                        "name": "systenant"
                    }
                },
                "period_end": "2012-01-01T00:00:00Z"
            },
            "/projects-all/2012": {
                "period_start": "2012-01-01T00:00:00Z",
                "projects": {
                    "tenant12": {
                        "url": "http://localhost:80/projects/tenant12",
                        "usage": {
                            "memory_mb": 0.0,
                            "vcpus": 0.0,
                            "local_gb": 0.0
                        },
                        "running": 0,
                        "instances_count": 0,
                        "name": "tenant12"
                    },
                    "systenant": {
                        "url": "http://localhost:80/projects/systenant",
                        "usage": {
                            "memory_mb": 0.0,
                            "vcpus": 0.0,
                            "local_gb": 0.0
                        },
                        "running": 0,
                        "instances_count": 0,
                        "name": "systenant"
                    }
                },
                "period_end": "2013-01-01T00:00:00Z"
            },
            "/projects/tenant12/2011/1": {
                "project": {
                    "instances_count": 2,
                    "name": "tenant12",
                    "url": "http://localhost:80/projects/tenant12",
                    "instances": [
                        {
                            "instance_id": 67,
                            "usage": {
                                "memory_mb": 356400,
                                "vcpus": 10800,
                                "local_gb": 205200
                            },
                            "running": 1846800,
                            "created_at": "2011-02-01T00:00:00Z",
                            "destroyed_at": "2011-02-03T00:00:00Z"
                        },
                        {
                            "instance_id": 54,
                            "usage": {
                                "memory_mb": 237600,
                                "vcpus": 140400,
                                "local_gb": 262800
                            },
                            "running": 399600,
                            "created_at": "2011-01-01T00:00:00Z",
                            "destroyed_at": "2011-01-02T00:00:00Z"
                        }
                    ],
                    "running": 624.0,
                    "usage": {
                        "memory_mb": 165.0,
                        "vcpus": 42.0,
                        "local_gb": 130.0
                    }
                },
                "period_start": "2011-01-01T00:00:00Z",
                "period_end": "2011-02-01T00:00:00Z"
            },
            "/projects/tenant12/2011/1/1": {
                "project": {
                    "instances_count": 1,
                    "name": "tenant12",
                    "url": "http://localhost:80/projects/tenant12",
                    "instances": [
                        {
                            "instance_id": 54,
                            "usage": {
                                "memory_mb": 237600,
                                "vcpus": 140400,
                                "local_gb": 262800
                            },
                            "running": 399600,
                            "created_at": "2011-01-01T00:00:00Z",
                            "destroyed_at": "2011-01-02T00:00:00Z"
                        }
                    ],
                    "running": 111.0,
                    "usage": {
                        "memory_mb": 66.0,
                        "vcpus": 39.0,
                        "local_gb": 73.0
                    }
                },
                "period_start": "2011-01-01T00:00:00Z",
                "period_end": "2011-01-02T00:00:00Z"
            },
            "/projects/tenant12/2011": {
                "project": {
                    "url": "http://localhost:80/projects/tenant12",
                    "usage": {
                        "memory_mb": 165.0,
                        "vcpus": 42.0,
                        "local_gb": 130.0
                    },
                    "running": 624.0,
                    "instances_count": 2,
                    "name": "tenant12"
                },
                "period_start": "2011-01-01T00:00:00Z",
                "period_end": "2012-01-01T00:00:00Z"
            },
        }
        fake_db_api = FakeDbApi()
        for func_name in ("instances_on_interval", ):
            self.stubs.Set(db_api, func_name, getattr(fake_db_api, func_name))
        for query in rest_calls:
            result = webob.Request.blank(query).get_response(rest.BillingApplication())
            self.assertEqual(json.loads(result.body), rest_calls[query])
        self.stubs.UnsetAll()
