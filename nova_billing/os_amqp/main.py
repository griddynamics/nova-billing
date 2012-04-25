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

from nova_billing.os_amqp import amqp
from nova_billing.utils import global_conf


def main():
    global_conf.logging()
    global_conf.load_nova_conf()
    service = amqp.Service()
    service.start()
    service.wait()


if __name__ == '__main__':
    main()
