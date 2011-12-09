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
Nova Billing API.
"""

from datetime import datetime

from nova_billing.db.sqlalchemy import models
from nova_billing.db.sqlalchemy.session import get_session

from nova import flags
from nova import utils


FLAGS = flags.FLAGS


def _parse_datetime(dtstr):
    if not dtstr:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.strptime(dtstr, fmt)
        except ValueError:
            pass
    return None


def instance_event_create(values):
    instance_event_ref = models.InstanceEvent()
    instance_event_ref.update(values)
    instance_event_ref.save()
    return instance_event_ref


def instance_event_get(filter):
    session = get_session()
    query = session.query(models.InstanceEvent)

    filter_fields = ("user_id",
               "project_id",
               "instance_id",
               "instance_type",
               "event")
    filter_dict = {}
    for field in filter_fields:
        if field in filter:
            filter_dict[field] = filter[field]

    if filter_dict:
        query = query.filter_by(**filter_dict)
    date = _parse_datetime(filter.get("start", None))
    if date:
        query = query.filter(models.InstanceEvent.datetime>=date)
    date = _parse_datetime(filter.get("end", None))
    if date:
        query = query.filter(models.InstanceEvent.datetime<=date)
    result = query.all()
    return result
