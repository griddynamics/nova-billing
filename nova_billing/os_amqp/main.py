#!/usr/bin/python
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

"""Starter script for Billing OS AMPQ binder."""

import eventlet
eventlet.monkey_patch()

import os
import sys


possible_topdir = os.path.normpath(os.path.join(os.path.abspath(
        sys.argv[0]), os.pardir, os.pardir))
if os.path.exists(os.path.join(possible_topdir, "nova", "__init__.py")):
    sys.path.insert(0, possible_topdir)


from nova import flags
from nova import wsgi
from nova import log as logging
from nova import service
from nova import utils

from nova_billing.os_amqp import amqp

def main():
    utils.default_flagfile()
    flags.FLAGS(sys.argv)
    logging.setup()
#    utils.monkey_patch()
    service.serve(amqp.Service())
    service.wait()


if __name__ == '__main__':
    main()
