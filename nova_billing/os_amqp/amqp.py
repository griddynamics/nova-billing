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
OpenStack AMQP listener
"""

import time
import socket
import logging

import eventlet

import kombu.entity
import kombu.messaging
import kombu.connection

from nova_billing import utils
from nova_billing.utils import global_conf

from . import instances
from . import volumes


LOG = logging.getLogger(__name__)


class Service(object):
    billing_heart = utils.get_heart_client()
    heart_request_interceptors = (
        instances.create_heart_request,
        volumes.create_heart_request,                                  
    )
    """
    Class of AMQP listening service.
    Usually this service starts at the beginning of the billing daemon
    and starts listening immediately. In case of connection errors
    reconnection attempts will be made periodically.
    
    The service listens for ``compute.#`` routing keys.
    """
    def __init__(self):
        self.params = dict(hostname=global_conf.rabbit_host,
                          port=global_conf.rabbit_port,
                          userid=global_conf.rabbit_userid,
                          password=global_conf.rabbit_password,
                          virtual_host=global_conf.rabbit_virtual_host)
        self.connection = None

    def reconnect(self):
        if self.connection:
            try:
                self.connection.close()
            except self.connection.connection_errors:
                pass
            time.sleep(1)

        self.connection = kombu.connection.BrokerConnection(**self.params)

        options = {
            "durable": global_conf.rabbit_durable_queues,
            "auto_delete": False,
            "exclusive": False
        }

        exchange = kombu.entity.Exchange(
                name=global_conf.control_exchange,
                type="topic",
                durable=options["durable"],
                auto_delete=options["auto_delete"])
        self.channel = self.connection.channel()

        self.queue = kombu.entity.Queue(
            name="nova_billing",
            exchange=exchange,
            routing_key="compute.#",
            channel=self.channel,
            **options)
        LOG.debug("Created kombu connection: %s" % self.params)

    def process_message(self, body, message):
        try:
            self.process_event(body, message)
        except:
            LOG.exception("Cannot handle message")
        message.ack()

    def process_event(self, body, message):
        """
        This function analyzes ``body`` and calls
        heart_request_interceptors.
        """
        method = body.get("method", None)
        heart_request = None
        for interceptor in self.heart_request_interceptors:
            heart_request = interceptor(method, body)
            if heart_request is not None:
                heart_request.setdefault("datetime", utils.datetime_to_str(
                    self.get_event_datetime(body)))
                heart_request.setdefault("account", body["_context_project_id"])
                try:
                    self.billing_heart.event(heart_request)
                except socket.error as ex:
                    LOG.error("cannot post event to the Heart: %s" % str(ex))
                except:
                    LOG.exception("cannot post event to the Heart")
                break
        try:
            routing_key = message.delivery_info["routing_key"]
        except AttributeError, KeyError:
            routing_key = "<unknown>"
        LOG.debug("routing_key=%s method=%s" % (routing_key, method))

    def get_event_datetime(self, body):
        return utils.now()

    def consume(self):
        """
        Get messages in an infinite loop. This is the main function of service's green thread.
        """
        while True:
            try:
                self.reconnect()
                with kombu.messaging.Consumer(
                    channel=self.channel,
                    queues=self.queue,
                    callbacks=[self.process_message]) as consumer:
                    while True:
                        self.connection.drain_events()
            except socket.error:
                pass
            except Exception, e:
                LOG.exception('Failed to consume message from queue: %s' % str(e))

    def start(self):
        self.server = eventlet.spawn(self.consume)

    def stop(self):
        self.server.stop()

    def wait(self):
        self.server.wait()
