# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 Grid Dynamics Consulting Services, Inc, All Rights Reserved
#  http://www.griddynamics.com
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
#  FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#  SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#  OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
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
                 "12": {"created_at": datetime.datetime(2011, 1, 1),
                        "destroyed_at": datetime.datetime(2011, 1, 2),
                        "running": 1, "price": 2},
                 "14": {"created_at": datetime.datetime(2011, 1, 4),
                        "destroyed_at": datetime.datetime(2011, 2, 1),
                        "running": 13, "price": 14},
            },
            "tenant12": {
                 "54": {"created_at": datetime.datetime(2011, 1, 1),
                        "destroyed_at": datetime.datetime(2011, 1, 2),
                        "running": 111, "price": 112},
                 "67": {"created_at": datetime.datetime(2011, 2, 1),
                        "destroyed_at": datetime.datetime(2011, 2, 3),
                        "running": 513, "price": 514},
                 "90": {"created_at": datetime.datetime(2013, 3, 4),
                        "destroyed_at": datetime.datetime(2013, 5, 6),
                        "running": 1013, "price": 1014},
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
            "/projects-all/2011": {
                "date": "2011-01-01T00:00:00", 
                "duration": "year", 
                "projects": {
                    "systenant": {
                        "instances_count": 2, 
                        "name": "systenant", 
                        "price": 16, 
                        "running": 14, 
                        "url": "http://localhost:80/projects/systenant"
                    }, 
                    "tenant12": {
                        "instances_count": 2, 
                        "name": "tenant12", 
                        "price": 626, 
                        "running": 624, 
                        "url": "http://localhost:80/projects/tenant12"
                    }
                }
            }, 
            "/projects-all/2011/01": {
                "date": "2011-01-01T00:00:00", 
                "duration": "month", 
                "projects": {
                    "systenant": {
                        "instances": {
                            "12": {
                                "created_at": "2011-01-01T00:00:00", 
                                "destroyed_at": "2011-01-02T00:00:00", 
                                "name": "12", 
                                "price": 2, 
                                "running": 1
                            }, 
                            "14": {
                                "created_at": "2011-01-04T00:00:00", 
                                "destroyed_at": "2011-02-01T00:00:00", 
                                "name": "14", 
                                "price": 14, 
                                "running": 13
                            }
                        }, 
                        "instances_count": 2, 
                        "name": "systenant", 
                        "price": 16, 
                        "running": 14, 
                        "url": "http://localhost:80/projects/systenant"
                    }, 
                    "tenant12": {
                        "instances": {
                            "54": {
                                "created_at": "2011-01-01T00:00:00", 
                                "destroyed_at": "2011-01-02T00:00:00", 
                                "name": "54", 
                                "price": 112, 
                                "running": 111
                            }, 
                            "67": {
                                "created_at": "2011-02-01T00:00:00", 
                                "destroyed_at": "2011-02-03T00:00:00", 
                                "name": "67", 
                                "price": 514, 
                                "running": 513
                            }
                        }, 
                        "instances_count": 2, 
                        "name": "tenant12", 
                        "price": 626, 
                        "running": 624, 
                        "url": "http://localhost:80/projects/tenant12"
                    }
                }
            }, 
            "/projects-all/2011/1/1": {
                "date": "2011-01-01T00:00:00", 
                "duration": "day", 
                "projects": {
                    "systenant": {
                        "instances": {
                            "12": {
                                "created_at": "2011-01-01T00:00:00", 
                                "destroyed_at": "2011-01-02T00:00:00", 
                                "name": "12", 
                                "price": 2, 
                                "running": 1
                            }
                        }, 
                        "instances_count": 1, 
                        "name": "systenant", 
                        "price": 2, 
                        "running": 1, 
                        "url": "http://localhost:80/projects/systenant"
                    }, 
                    "tenant12": {
                        "instances": {
                            "54": {
                                "created_at": "2011-01-01T00:00:00", 
                                "destroyed_at": "2011-01-02T00:00:00", 
                                "name": "54", 
                                "price": 112, 
                                "running": 111
                            }
                        }, 
                        "instances_count": 1, 
                        "name": "tenant12", 
                        "price": 112, 
                        "running": 111, 
                        "url": "http://localhost:80/projects/tenant12"
                    }
                }
            }, 
            "/projects/tenant12/2011": {
                "date": "2011-01-01T00:00:00", 
                "duration": "year", 
                "projects": {
                    "tenant12": {
                        "instances_count": 2, 
                        "name": "tenant12", 
                        "price": 626, 
                        "running": 624, 
                        "url": "http://localhost:80/projects/tenant12"
                    }
                }
            }, 
            "/projects/tenant12/2011/1": {
                "date": "2011-01-01T00:00:00", 
                "duration": "month", 
                "projects": {
                    "tenant12": {
                        "instances": {
                            "54": {
                                "created_at": "2011-01-01T00:00:00", 
                                "destroyed_at": "2011-01-02T00:00:00", 
                                "name": "54", 
                                "price": 112, 
                                "running": 111
                            }, 
                            "67": {
                                "created_at": "2011-02-01T00:00:00", 
                                "destroyed_at": "2011-02-03T00:00:00", 
                                "name": "67", 
                                "price": 514, 
                                "running": 513
                            }
                        }, 
                        "instances_count": 2, 
                        "name": "tenant12", 
                        "price": 626, 
                        "running": 624, 
                        "url": "http://localhost:80/projects/tenant12"
                    }
                }
            }, 
            "/projects/tenant12/2011/1/1": {
                "date": "2011-01-01T00:00:00", 
                "duration": "day", 
                "projects": {
                    "tenant12": {
                        "instances": {
                            "54": {
                                "created_at": "2011-01-01T00:00:00", 
                                "destroyed_at": "2011-01-02T00:00:00", 
                                "name": "54", 
                                "price": 112, 
                                "running": 111
                            }
                        }, 
                        "instances_count": 1, 
                        "name": "tenant12", 
                        "price": 112, 
                        "running": 111, 
                        "url": "http://localhost:80/projects/tenant12"
                    }
                }
            }
        }
        fake_db_api = FakeDbApi()
        for func_name in ("instances_on_interval", ):
            self.stubs.Set(db_api, func_name, getattr(fake_db_api, func_name))
        for query in rest_calls:
            result = webob.Request.blank(query).get_response(rest.BillingApplication())
            self.assertEqual(json.loads(result.body), rest_calls[query])
        self.stubs.UnsetAll()
