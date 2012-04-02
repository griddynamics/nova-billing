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
AMQP listener
"""
from nova import flags
from nova import log as logging
from nova_billing import interceptors
from nova_billing.ampq_listener import Listener


LOG = logging.getLogger("nova_billing.ampq_listeners")
FLAGS = flags.FLAGS


class Service(object):
    """
    Class of AMQP listening service.
    Usually this service starts at the beginning of the billing daemon
    and starts listening immediately. In case of connection errors
    reconnection attempts will be made periodically.
    
    The service listens for ``compute.#`` routing keys.
    """
    def __init__(self):
        self.listeners = [Listener('compute.#', interceptors.instance, interceptors.local_volume)]

    def start(self):
        for listener in self.listeners:
            listener.listen()

    def stop(self):
        for listener in self.listeners:
            listener.stop()

    def wait(self):
        for listener in self.listeners:
            listener.wait()
