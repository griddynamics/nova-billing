#!/usr/bin/env python
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


import gettext
import glob
import os
import subprocess
import sys

from setuptools import setup, find_packages


setup(name='nova-billing',
      version='2011.3',
      license='GNU GPL v3',
      description='cloud computing fabric controller',
      author='Alessio Ababilov, Ivan Kolodyazhny (GridDynamics Openstack Core Team, (c) GridDynamics)',
      author_email='openstack@griddynamics.com',
      url='http://www.griddynamics.com/openstack',
      packages=find_packages(exclude=['bin', 'smoketests', 'tests']),
      scripts=['bin/nova-billing'],
      py_modules=[],
      test_suite='tests'
)

