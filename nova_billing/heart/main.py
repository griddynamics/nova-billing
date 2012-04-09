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

"""Starter script for Nova Billing heart."""

import argparse
import logging

from nova_billing.heart import rest
from nova_billing.heart.database import db


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--no-reload", "-r", default=False,
                            action="store_true", help="do not reload")
    arg_parser.add_argument("host:port", nargs="?",
                            default="127.0.0.1:8080", help="host:port")
    args = arg_parser.parse_args()
    
    logging.basicConfig(level=logging.DEBUG)
    db.create_all()
    from nova_billing.heart import app
    listen = getattr(args, "host:port").split(':')
    app.debug = True
    app.run(host=listen[0], port=int(listen[1]), use_reloader=not args.no_reload)


if __name__ == '__main__':
    main()
