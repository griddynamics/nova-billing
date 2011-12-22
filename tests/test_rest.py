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
from nova_billing.db import api as db_api

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tests


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


class TestCase(tests.TestCase):
    def test_billing_application(self):
        """
        Test different billing REST API queries.
        """
        rest_calls = {
            "/": {
                "application": "nova-billing",
                "version": "0.0.2",
                "urls": {
                    "projects-all": "http://localhost:80/projects-all",
                    "projects": "http://localhost:80/projects"
                }
            },
            "/projects": {
                "period_start": "2011-12-01T00:00:00Z",
                "projects": {
                    "tenant12": {
                        "url": "http://localhost:80/projects/tenant12",
                        "usage": {
                            "local_gb_h": 0.0,
                            "vcpus_h": 0.0,
                            "memory_mb_h": 0.0
                        },
                        "instances_count": 0,
                        "running_sec": 0,
                        "name": "tenant12"
                    },
                    "systenant": {
                        "url": "http://localhost:80/projects/systenant",
                        "usage": {
                            "local_gb_h": 0.0,
                            "vcpus_h": 0.0,
                            "memory_mb_h": 0.0
                        },
                        "instances_count": 0,
                        "running_sec": 0,
                        "name": "systenant"
                    }
                },
                "period_end": "2012-01-01T00:00:00Z"
            },
            "/projects-all": {
                "period_start": "2011-12-01T00:00:00Z",
                "projects": {
                    "tenant12": {
                        "url": "http://localhost:80/projects/tenant12",
                        "usage": {
                            "local_gb_h": 0.0,
                            "vcpus_h": 0.0,
                            "memory_mb_h": 0.0
                        },
                        "instances_count": 0,
                        "running_sec": 0,
                        "name": "tenant12"
                    },
                    "systenant": {
                        "url": "http://localhost:80/projects/systenant",
                        "usage": {
                            "local_gb_h": 0.0,
                            "vcpus_h": 0.0,
                            "memory_mb_h": 0.0
                        },
                        "instances_count": 0,
                        "running_sec": 0,
                        "name": "systenant"
                    }
                },
                "period_end": "2012-01-01T00:00:00Z"
            },
            "/projects-all/2011": {
                "period_start": "2011-01-01T00:00:00Z",
                "projects": {
                    "tenant12": {
                        "url": "http://localhost:80/projects/tenant12",
                        "usage": {
                            "local_gb_h": 130.0,
                            "vcpus_h": 42.0,
                            "memory_mb_h": 165.0
                        },
                        "instances_count": 2,
                        "running_sec": 2246400,
                        "name": "tenant12"
                    },
                    "systenant": {
                        "url": "http://localhost:80/projects/systenant",
                        "usage": {
                            "local_gb_h": 79.0,
                            "vcpus_h": 80.0,
                            "memory_mb_h": 55.0
                        },
                        "instances_count": 2,
                        "running_sec": 50400,
                        "name": "systenant"
                    }
                },
                "period_end": "2012-01-01T00:00:00Z"
            },
            "/projects-all/2011/01": {
                "period_start": "2011-01-01T00:00:00Z",
                "projects": {
                    "tenant12": {
                        "url": "http://localhost:80/projects/tenant12",
                        "usage": {
                            "local_gb_h": 130.0,
                            "vcpus_h": 42.0,
                            "memory_mb_h": 165.0
                        },
                        "instances_count": 2,
                        "running_sec": 2246400,
                        "name": "tenant12"
                    },
                    "systenant": {
                        "url": "http://localhost:80/projects/systenant",
                        "usage": {
                            "local_gb_h": 79.0,
                            "vcpus_h": 80.0,
                            "memory_mb_h": 55.0
                        },
                        "instances_count": 2,
                        "running_sec": 50400,
                        "name": "systenant"
                    }
                },
                "period_end": "2011-02-01T00:00:00Z"
            },
            "/projects-all/2011/1/1": {
                "period_start": "2011-01-01T00:00:00Z",
                "projects": {
                    "tenant12": {
                        "url": "http://localhost:80/projects/tenant12",
                        "usage": {
                            "local_gb_h": 73.0,
                            "vcpus_h": 39.0,
                            "memory_mb_h": 66.0
                        },
                        "instances_count": 1,
                        "running_sec": 399600,
                        "name": "tenant12"
                    },
                    "systenant": {
                        "url": "http://localhost:80/projects/systenant",
                        "usage": {
                            "local_gb_h": 12.0,
                            "vcpus_h": 39.0,
                            "memory_mb_h": 45.0
                        },
                        "instances_count": 1,
                        "running_sec": 3600,
                        "name": "systenant"
                    }
                },
                "period_end": "2011-01-02T00:00:00Z"
            },
            "/projects-all/2012": {
                "period_start": "2012-01-01T00:00:00Z",
                "projects": {
                    "tenant12": {
                        "url": "http://localhost:80/projects/tenant12",
                        "usage": {
                            "local_gb_h": 0.0,
                            "vcpus_h": 0.0,
                            "memory_mb_h": 0.0
                        },
                        "instances_count": 0,
                        "running_sec": 0,
                        "name": "tenant12"
                    },
                    "systenant": {
                        "url": "http://localhost:80/projects/systenant",
                        "usage": {
                            "local_gb_h": 0.0,
                            "vcpus_h": 0.0,
                            "memory_mb_h": 0.0
                        },
                        "instances_count": 0,
                        "running_sec": 0,
                        "name": "systenant"
                    }
                },
                "period_end": "2013-01-01T00:00:00Z"
            },
            "/projects/systenant": {
                "project": {
                    "instances_count": 0,
                    "name": "systenant",
                    "url": "http://localhost:80/projects/systenant",
                    "instances": [],
                    "usage": {
                        "local_gb_h": 0.0,
                        "vcpus_h": 0.0,
                        "memory_mb_h": 0.0
                    },
                    "running_sec": 0
                },
                "period_start": "2011-12-01T00:00:00Z",
                "period_end": "2012-01-01T00:00:00Z"
            },
            "/projects/tenant12/2011": {
                "project": {
                    "url": "http://localhost:80/projects/tenant12",
                    "usage": {
                        "local_gb_h": 130.0,
                        "vcpus_h": 42.0,
                        "memory_mb_h": 165.0
                    },
                    "instances_count": 2,
                    "running_sec": 2246400,
                    "name": "tenant12"
                },
                "period_start": "2011-01-01T00:00:00Z",
                "period_end": "2012-01-01T00:00:00Z"
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
                                "local_gb_h": 57.0,
                                "vcpus_h": 3.0,
                                "memory_mb_h": 99.0
                            },
                            "created_at": "2011-02-01T00:00:00Z",
                            "running_sec": 1846800,
                            "destroyed_at": "2011-02-03T00:00:00Z"
                        },
                        {
                            "instance_id": 54,
                            "usage": {
                                "local_gb_h": 73.0,
                                "vcpus_h": 39.0,
                                "memory_mb_h": 66.0
                            },
                            "created_at": "2011-01-01T00:00:00Z",
                            "running_sec": 399600,
                            "destroyed_at": "2011-01-02T00:00:00Z"
                        }
                    ],
                    "usage": {
                        "local_gb_h": 130.0,
                        "vcpus_h": 42.0,
                        "memory_mb_h": 165.0
                    },
                    "running_sec": 2246400
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
                                "local_gb_h": 73.0,
                                "vcpus_h": 39.0,
                                "memory_mb_h": 66.0
                            },
                            "created_at": "2011-01-01T00:00:00Z",
                            "running_sec": 399600,
                            "destroyed_at": "2011-01-02T00:00:00Z"
                        }
                    ],
                    "usage": {
                        "local_gb_h": 73.0,
                        "vcpus_h": 39.0,
                        "memory_mb_h": 66.0
                    },
                    "running_sec": 399600
                },
                "period_start": "2011-01-01T00:00:00Z",
                "period_end": "2011-01-02T00:00:00Z"
            },
        }
        fake_db_api = FakeDbApi()
        for func_name in ("instances_on_interval", ):
            self.stubs.Set(db_api, func_name, getattr(fake_db_api, func_name))
        self.stubs.Set(rest, "get_current_datetime", lambda: datetime.datetime(2011, 12, 1))
        for query in rest_calls:
            result = webob.Request.blank(query).get_response(rest.BillingApplication())
            self.assertEqual(json.loads(result.body), rest_calls[query])
