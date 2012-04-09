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
Miscellaneous utility functions:

- usage calculations for different VM states;
- datetime manipulations;
- other.
"""

from datetime import datetime
from nova_billing.client import BillingHeartClient


class ContextType(object):
    JSON = "application/json"


def total_seconds(td):
    """This function is added for portability
    because timedelta.total_seconds() 
    was introduced only in python 2.7."""
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6


def now():
    """
    Return current time in UTC.
    """
    return datetime.utcnow()


def str_to_datetime(dtstr):
    """
    Convert string to datetime.datetime. String should be in ISO 8601 format.
    The function returns ``None`` for invalid date string.
    """
    if not dtstr:
        return None
    if dtstr.endswith("Z"):
        dtstr = dtstr[:-1]
    for fmt in ("%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.strptime(dtstr, fmt)
        except ValueError:
            pass
    return None


def datetime_to_str(dt):
    """
    Convert datetime.datetime instance to string.
    Used for JSONization.
    """
    return ("%sZ" % dt.isoformat()) if dt else None


def usage_to_hours(usage):
    """
    Convert usage measured for seconds to hours.
    """
    return dict([(key + "_h", usage[key] / 3600.0) for key in usage])


def dict_add(a, b):
    """
    Increment all keys in ``a`` on keys in ``b``.
    """
    for key in b:
        a[key] = a.get(key, 0) + b[key]


def cost_add(cost, begin_at, end_at):
    return cost if cost < 0 else cost * total_seconds(end_at - begin_at)


try:
    from nova import flags
    FLAGS = flags.FLAGS
except ImportError:
    FLAGS = object()


class GlobalConf(object):
    admin_token = "999888777666"
    billing_heart_url = "http://localhost:8080"
    nova_url = "http://127.0.0.1:8774/v1.1"
    keystone_url = "http://127.0.0.1:35357/v2.0"

    def __getattr__(self, name):
        try:
            return getattr(FLAGS, name)
        except AttributeError:
            pass
        raise AttributeError(name)
    

global_conf = GlobalConf()


def get_heart_client():
    return BillingHeartClient(
        management_url=global_conf.billing_heart_url) 


def get_nova_client():
    from novaclient.v1_1 import Client
    client = Client("", "", "", "")
    client.client.auth_token = global_conf.admin_token
    client.client.management_url = global_conf.nova_url
    return client


def get_keystone_client():
    from keystoneclient.v2_0 import client as keystone_client
    client = keystone_client.Client(
            endpoint=global_conf.keystone_url,
            token=global_conf.admin_token)
    return client

