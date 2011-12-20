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

"""
AMQP listener
"""

import os
import sys
import time
import socket
from datetime import datetime

import eventlet
import json

import kombu
import kombu.entity
import kombu.messaging
import kombu.connection

from nova import exception
from nova import flags
from nova import log as logging

from nova_billing import vm_states
from nova_billing.db import api as db_api


LOG = logging.getLogger("nova_billing.amqp_listener")
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
        self.params = dict(hostname=FLAGS.rabbit_host,
                          port=FLAGS.rabbit_port,
                          userid=FLAGS.rabbit_userid,
                          password=FLAGS.rabbit_password,
                          virtual_host=FLAGS.rabbit_virtual_host)
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
            "durable": FLAGS.rabbit_durable_queues,
            "auto_delete": False,
            "exclusive": False
        }

        exchange = kombu.entity.Exchange(
                name=FLAGS.control_exchange,
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
        LOG.debug("created kombu connection: %s" % self.params)

    def process_message(self, body, message):
        try:
            self.process_event(body, message)
        except KeyError, ex:
            LOG.exception("cannot handle message")
        message.ack()

    def process_event(self, body, message):
        """
        This function analyzes ``body`` and saves
        event information to the database.
        """
        method = body.get("method", None)
        instance_segment = None
        descr = ""
        if method == "run_instance":
            instance_info = {
                "project_id": body["args"]["request_spec"]
                    ["instance_properties"]["project_id"],
                "instance_id": body["args"]["instance_id"],
            }
            instance_type = body["args"]["request_spec"]["instance_type"]
            for key in "local_gb", "memory_mb", "vcpus":
                instance_info[key] = instance_type[key]
            instance_info_ref = db_api.instance_info_create(instance_info)

            instance_segment = {
                "instance_info_id": instance_info_ref.id,
                "segment_type": vm_states.ACTIVE,
            }

            descr = " instance info %s" % json.dumps(instance_info)
        elif method == "terminate_instance":
            pass
        elif method == "start_instance":
            instance_segment = {
                "segment_type": vm_states.ACTIVE,
            }
        elif method == "stop_instance":
            instance_segment = {
                "segment_type": vm_states.STOPPED,
            }
        elif method == "unpause_instance":
            instance_segment = {
                "segment_type": vm_states.ACTIVE,
            }
        elif method == "pause_instance":
            instance_segment = {
                "segment_type": vm_states.PAUSED,
            }
        elif method == "resume_instance":
            instance_segment = {
                "segment_type": vm_states.ACTIVE,
            }
        elif method == "suspend_instance":
            instance_segment = {
                "segment_type": vm_states.SUSPENDED,
            }
        else:
            return

        event_datetime = self.get_event_datetime(body)
        db_api.instance_segment_end(body["args"]["instance_id"], event_datetime)
        if instance_segment:
            instance_segment["begin_at"] = event_datetime
            if not instance_segment.has_key("instance_info_id"):
                instance_segment["instance_info_id"] = \
                    db_api.instance_info_get_latest(body["args"]["instance_id"])
            db_api.instance_segment_create(instance_segment)
        try:
            routing_key = message.delivery_info["routing_key"]
        except AttributeError, KeyError:
            routing_key = "<unknown>"
        LOG.debug("routing_key=%s method=%s%s" % (routing_key, method, descr))

    def get_event_datetime(self, body):
        return datetime.utcnow()

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
                LOG.exception(_('Failed to consume message from queue: '
                        '%s' % str(e)))

    def start(self):
        self.server = eventlet.spawn(self.consume)

    def stop(self):
        self.server.stop()

    def wait(self):
        self.server.wait()
