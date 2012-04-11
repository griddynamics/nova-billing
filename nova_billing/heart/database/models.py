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

import json

from flaskext.sqlalchemy import SQLAlchemy

from . import db


TypeLength = 16


class BillingBase(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)


class Account(db.Model, BillingBase):
    __tablename__ = "account"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)


class Resource(db.Model, BillingBase):
    __tablename__ = "resource"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255))
    rtype = db.Column(db.String(TypeLength), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("resource.id"))
    attrs = db.Column(db.UnicodeText)
    
    def get_attrs(self):
        if self.attrs:
            try:
                return json.loads(self.attrs)
            except:
                return {}
        return {}

    def set_attrs(self, attrs):
        self.attrs = json.dumps(attrs)


class Segment(db.Model, BillingBase):
    __tablename__ = "segment"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    resource_id = db.Column(db.Integer, db.ForeignKey("resource.id"), nullable=False)
    
    # positive: linear (must multiply on time)
    # zero: free of charge
    # negative: fixed cost
    cost = db.Column(db.Float, nullable=False)
    begin_at = db.Column(db.DateTime, nullable=False)
    end_at = db.Column(db.DateTime, nullable=True)


class Tariff(db.Model, BillingBase):
    __tablename__ = "tariff"
    rtype = db.Column(db.String(TypeLength), nullable=False, primary_key=True)
    multiplier = db.Column(db.Float, nullable=False)
