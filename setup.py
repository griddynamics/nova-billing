#!/usr/bin/env python
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


import gettext
import glob
import os
import subprocess
import sys

from setuptools import setup, find_packages


ROOT = os.path.dirname(__file__)
sys.path.append(ROOT)


from nova_billing.version import version_string


setup(name='nova-billing',
      version=version_string(),
      license='GNU GPL v3',
      description='cloud computing fabric controller',
      author='Alessio Ababilov, Ivan Kolodyazhny (GridDynamics Openstack Core Team, (c) GridDynamics)',
      author_email='openstack@griddynamics.com',
      url='http://www.griddynamics.com/openstack',
      packages=find_packages(exclude=['bin', 'smoketests', 'tests']),
      entry_points={
        'console_scripts': [
            'nova-billing-heart = nova_billing.heart.main:main',
            'nova-billing-os-amqp = nova_billing.os_amqp.main:main',
        ]
      },
      py_modules=[],
      test_suite='tests'
)

