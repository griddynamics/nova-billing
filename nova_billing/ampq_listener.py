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
import socket

__author__ = 'bfilippov'
import eventlet
import kombu
import kombu.entity
import kombu.messaging
import kombu.connection
import time

from nova.flags import FLAGS
from nova import log as logging

LOG =  logging.getLogger('nova_billing.listener')

class Listener(object):

    def __init__(self, route, *interceptors):
        self.route = route
        self.interceptors = interceptors
        self.watchmen = None

        self.params = dict(hostname=FLAGS.rabbit_host,
                          port=FLAGS.rabbit_port,
                          userid=FLAGS.rabbit_userid,
                          password=FLAGS.rabbit_password,
                          virtual_host=FLAGS.rabbit_virtual_host)
        self.connection = None

    def connect(self):
        if self.connection:
            try:
                self.connection.close()
            except self.connection.connection_errors:
                pass
            time.sleep(1)

        self.connection = kombu.connection.BrokerConnection(**self.params)

        options = {
            "durable": FLAGS.rabbit_durable_queues,
            "auto_delete": False,
            "exclusive": False
        }

        exchange = kombu.entity.Exchange(
                name=FLAGS.control_exchange,
                type="topic",
                durable=options["durable"],
                auto_delete=False)
        self.channel = self.connection.channel()

        self.queue = kombu.entity.Queue(
            name="nova_billing<%s>" % repr(self),
            exchange=exchange,
            routing_key=self.route,
            channel=self.channel,
            **options)
        LOG.debug("Created kombu connection: %s" % self.params)

    def _process_message(self, body, message):
        try:
            self._do_billing(body, message)
        except KeyError as e:
            LOG.exception("Cannot handle message %s" % e)
        message.ack()

    def _do_billing(self, body, message):
        """
        This function analyzes ``body`` and saves
        event information to the database.
        """
        method = body.get("method", None)
        found = False
        for interceptor in self.interceptors:
            f = interceptor.get(method)
            if f:
                f(body, message)
                found = True
        if not found:
            raise KeyError("Unable to locate callback "
                           "for method %s in route %s", method, self.route)

    def _listen(self):
        """
        Get messages in an infinite loop. This is the main function of listener's green thread.
        """
        while True:
            try:
                self.connect()
                with kombu.messaging.Consumer(
                    channel=self.channel,
                    queues=self.queue,
                    callbacks=[self._process_message]):
                    while True:
                        self.connection.drain_events()
            except socket.error:
                pass
            except Exception, e:
                LOG.exception('Failed to consume message from queue: %s' % str(e))

    def listen(self):
        self.watchmen = eventlet.spawn(self._listen)

    def stop(self):
        self.watchmen.stop()

    def wait(self):
        self.watchmen.wait()
