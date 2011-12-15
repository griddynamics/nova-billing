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
SQLAlchemy models for Nova Billing.
"""

from sqlalchemy.orm import relationship, backref, object_mapper
from sqlalchemy import Column, Integer, String, schema
from sqlalchemy import ForeignKey, DateTime, Boolean, Text, Float
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import ForeignKeyConstraint

from nova_billing.db.sqlalchemy.session import get_session, get_engine

from nova import auth
from nova import exception
from nova import flags
from nova import utils


FLAGS = flags.FLAGS
BASE = declarative_base()


class NovaBillingBase(object):
    """Base class for Nova Billing Models."""
    _i = None

    def save(self, session=None):
        """Save this object."""

        if not session:
            session = get_session()
        session.add(self)
        try:
            session.flush()
        except IntegrityError:
            raise

    def delete(self, session=None):
        """Delete this object."""
        self.save(session=session)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)

    def __iter__(self):
        self._i = iter(object_mapper(self).columns)
        return self

    def next(self):
        n = self._i.next().name
        return n, getattr(self, n)

    def update(self, values):
        """Make the model object behave like a dict"""
        for k, v in values.iteritems():
            setattr(self, k, v)

    def iteritems(self):
        """Make the model object behave like a dict.

        Includes attributes from joins."""
        local = dict(self)
        joined = dict([(k, v) for k, v in self.__dict__.iteritems()
                      if not k[0] == '_'])
        local.update(joined)
        return local.iteritems()


class InstanceInfo(BASE, NovaBillingBase):
    __tablename__ = 'billing_instance_info'
    id = Column(Integer, primary_key=True, autoincrement=True)
    instance_id = Column(Integer, nullable=False)
    project_id = Column(String(255), nullable=True)
    local_gb = Column(Integer, nullable=True)
    memory_mb = Column(Integer, nullable=True)
    vcpus = Column(Integer, nullable=True)


class InstanceSegment(BASE, NovaBillingBase):
    __tablename__ = 'billing_instance_segment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    instance_info_id = Column(Integer, nullable=False)
    segment_type = Column(Integer, nullable=False)
    begin_at = Column(DateTime, nullable=False)
    end_at = Column(DateTime, nullable=True)


def register_models():
    """Register Models and create metadata."""
    models = (InstanceInfo, InstanceSegment)
    engine = get_engine()
    for model in models:
        model.metadata.create_all(engine)


def unregister_models():
    """Unregister Models, useful clearing out data before testing"""
    from nova_billing.db.sqlalchemy.session import _ENGINE
    assert _ENGINE
    BASE.metadata.drop_all(_ENGINE)

