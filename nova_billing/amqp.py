# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 Grid Dynamics Consulting Services, Inc, All Rights Reserved
#  http://www.griddynamics.com
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
#  FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#  SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#  OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
AMQP listener
"""

import os
import sys
import time
from datetime import datetime

import eventlet

import kombu
import kombu.entity
import kombu.messaging
import kombu.connection

from nova import exception
from nova import flags
from nova import log as logging

from nova_billing.db.sqlalchemy import api


LOG = logging.getLogger("nova_billing.amqp_listener")
FLAGS = flags.FLAGS


class Service(object):
    def __init__(self):
        self.params = dict(hostname=FLAGS.rabbit_host,
                          port=FLAGS.rabbit_port,
                          userid=FLAGS.rabbit_userid,
                          password=FLAGS.rabbit_password,
                          virtual_host=FLAGS.rabbit_virtual_host)

        LOG.debug("%s" % self.params)

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

    def process_message(self, body, message):
        try:
            self.log_inst_info(body, message)
        except Exception, ex:
            LOG.exception("cannot handle message")
        message.ack()

    def log_inst_info(self, inst_info, message):
        if inst_info.get("event_type", None) == "compute.instance.create":
            payload = inst_info.get("payload", {})
            event = "created"
        elif inst_info.get("event_type", None) == "compute.instance.delete":
            payload = inst_info.get("payload", {})
            event = "deleted"
        elif inst_info.get("method", None) == "run_instance":
            payload = inst_info["args"]["request_spec"]["instance_properties"].copy()
            payload["instance_id"] = inst_info["args"]["instance_id"]
            payload["instance_type"] = inst_info["args"]["request_spec"]["instance_type"]["name"]
            event = "run"
        elif inst_info.get("method", None) == "terminate_instance":
            payload = {"instance_id": inst_info["args"]["instance_id"]}
            for attr in "project_id", "user_id":
                payload[attr] = inst_info["_context_" + attr]
            event = "terminate"
        else:
            return

        routing_key = message.delivery_info["routing_key"]
        descr = "routing_key=%s event=%s" % (routing_key, event)
        event_attrs = {"datetime": datetime.today(), "event": event}
        for attr in ("instance_id", "project_id", "user_id", "instance_type"):
            try:
                event_attrs[attr] = payload[attr]
                descr += " %s=%s" % (attr, payload[attr])
            except:
                pass

        api.instance_event_create(event_attrs)
        LOG.debug(descr)

    def consume(self):
        with kombu.messaging.Consumer(
            channel=self.channel,
            queues=self.queue,
            callbacks=[self.process_message]) as consumer:
            while True:
                self.connection.drain_events()

    def start(self):
        self.server = eventlet.spawn(self.consume)

    def stop(self):
        self.server.stop()

    def wait(self):
        self.server.wait()
