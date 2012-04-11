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
Base class for Nova Billing unit tests.
"""

import unittest
import stubout
import json
import os


class TestCase(unittest.TestCase):
    def setUp(self):
        """Run before each test method to initialize test environment."""
        super(TestCase, self).setUp()
        self.stubs = stubout.StubOutForTesting()

    def tearDown(self):
        """Runs after each test method to tear down test environment."""
        self.stubs.UnsetAll()
        self.stubs.SmartUnsetAll()

    @staticmethod
    def json_load_from_file(filename):
        with open(os.path.join(os.path.dirname(
                os.path.abspath(__file__)), filename),
            "rt") as json_file:
            return json.load(json_file)

    #Set it to True for json out files regeneration
    write_json = False
    
    def json_check_with_file(self, data, filename):
        if self.write_json:
            with open(os.path.join(os.path.dirname(
                os.path.abspath(__file__)), filename),
            "wt") as json_file:
                json.dump(data, json_file, indent=4)
        else:
            self.assertEqual(data, 
                             self.json_load_from_file(filename))
        