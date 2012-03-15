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
Module for communication with Glance.
"""

from nova import flags
from nova.image.glance import pick_glance_api_server

from glance import client as glance_client

from nova_billing import utils


FLAGS = flags.FLAGS


def images_on_interval(period_start, period_stop, auth_tok, tenant_id=None):
    """
    Retrieve images statistics for the given interval [``period_start``, ``period_stop``]. 
    ``tenant_id=None`` means all projects.

    Example of the returned value:

    .. code-block:: python

        {
            "1": {
                12: {
                    "created_at": datetime.datetime(2011, 1, 1),
                    "destroyed_at": datetime.datetime(2011, 1, 2),
                    "name": "Gentoo initrd",
                    "usage": {"local_gb": 0.1},
                },
                14: {
                    "created_at": datetime.datetime(2011, 1, 4),
                    "destroyed_at": datetime.datetime(2011, 2, 1),
                    "name": "Ubuntu vmlinuz",
                    "usage": {"local_gb": 2.5},
                },
            },
            "2": {
                24: {
                    "created_at": datetime.datetime(2011, 1, 1),
                    "destroyed_at": datetime.datetime(2011, 1, 2),
                    "name": "RHEL vmlinuz",
                    "usage": {"local_gb": 6.1},
                },
            }
        }

    :returns: a dictionary where keys are project ids and values are project statistics.
    """

    glance_host, glance_port = pick_glance_api_server()
    client = glance_client.Client(glance_host, glance_port, auth_tok=auth_tok)
    images = client.get_images_detailed(filters={"is_public": "none"})
    if tenant_id:
        images = [image for image in images if image["owner"] == tenant_id]
    else:
        images = [image for image in images if image["owner"] is not None]
    report_by_id = {}
    now = utils.now()
    for image in images:
        created_at = utils.str_to_datetime(image["created_at"])
        if created_at >= period_stop:
            continue
        deleted_at = utils.str_to_datetime(image["deleted_at"])
        if deleted_at and deleted_at <= period_start:
            continue
        lifetime = utils.total_seconds(
            min(deleted_at or now, period_stop) -
            max(created_at, period_start))
        if lifetime < 0:
            lifetime = 0
        try:
            tenant_statistics = report_by_id[image["owner"]]
        except KeyError:
            tenant_statistics = {}
            report_by_id[image["owner"]] = tenant_statistics
        tenant_statistics[image["id"]] = {
            "name": image["name"],
            "created_at": created_at,
            "destroyed_at": deleted_at,
            "usage": {"local_gb": image["size"] * lifetime / 2 ** 30}
        }

    return report_by_id
