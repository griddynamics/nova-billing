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
    instance_info_id = Column(Integer, ForeignKey('billing_instance_info.id'), nullable=False)
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

