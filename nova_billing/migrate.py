#!/usr/bin/python2
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

import sys
import json

from sqlalchemy import create_engine
from flask import _request_ctx_stack

from nova_billing import utils
from nova_billing.utils import global_conf
from nova_billing import client
from nova_billing.heart.database import db
from nova_billing.heart.database import api as db_api
from nova_billing.heart.database.models import Segment


class ResourceTypes(object):
    Instance = "nova/instance"
    Image = "glance/image"


usage = "usage: python2 -m nova_billing.migrate [images|instances] URL"


def complain_usage():
    print >>sys.stderr, usage
    sys.exit(1)


def main():
    if len(sys.argv) < 3:
        complain_usage()

    _request_ctx_stack.push(1)
    db.create_all()
    if sys.argv[1] == "images":
        migrate_images(sys.argv[2])
    elif sys.argv[1] == "instances":
        migrate_instances(sys.argv[2])
    else:
        complain_usage()


def migrate_images(glance_url):
    glance_client = client.RestClient()
    glance_client.auth_headers = {"x-auth-token": global_conf.admin_token}
    glance_client.management_url = glance_url
    
    tariffs = db_api.tariff_map()
    accounts = {}
    images = json.loads(glance_client.get("/images/detail"))["images"]
    for project_id in (img1["owner"] for img1 in images):
        accounts[project_id] = \
            db_api.account_get_or_create(project_id).id
    
    for img1 in images:
        account_id = accounts[img1["owner"]]
        img2 = db_api.resource_get_or_create(
            account_id, None,
            ResourceTypes.Image,
            img1["id"]
        )
        seg = Segment(
            resource_id=img2.id,
            cost=img1["size"] * tariffs.get(ResourceTypes.Image, 1),
            begin_at=utils.str_to_datetime(img1["created_at"]),
            end_at=utils.str_to_datetime(img1["deleted_at"]))
        db.session.add(seg)

    db.session.commit()
    

def migrate_instances(old_db_url):
    engine1 = create_engine(old_db_url)

    tariffs = db_api.tariff_map()
    instance_resources = ("local_gb", "memory_mb", "vcpus")
    instance_info_attrs = (
        "id", "instance_id", "project_id",
        "local_gb", "memory_mb", "vcpus")
    instance_segment_attrs = (
        "id", "instance_info_id",
        "segment_type", "begin_at",
        "end_at")
    instance_infos = {}
    accounts = {}
    for inst1 in engine1.execute(
        "select distinct project_id from billing_instance_info"):
        accounts[inst1.project_id] = \
            db_api.account_get_or_create(inst1.project_id).id
    
    for inst1 in engine1.execute(
        "select %s from billing_instance_info" %
        ", ".join(instance_info_attrs)):
        account_id = accounts[inst1.project_id]
        inst2 = db_api.resource_get_or_create(
            account_id, None,
            ResourceTypes.Instance,
            inst1.instance_id
        )
        inst_dict = {
            "inst1": inst1,
            "inst2": inst2,
        }
        for rtype in instance_resources:
            inst_dict[rtype + "_id"] = db_api.resource_get_or_create(
                account_id, inst2.id, 
                rtype,
                None
            )
        instance_infos[inst1.id] = inst_dict
    
    for iseg in engine1.execute(
        "select %s from billing_instance_segment" %
        ", ".join(instance_segment_attrs)):
        inst_dict = instance_infos[iseg.instance_info_id]
        inst1 = inst_dict["inst1"]
        begin_at = utils.str_to_datetime(iseg.begin_at)
        end_at = utils.str_to_datetime(iseg.end_at)
        inst_dict["begin_at"] = (min(inst_dict["begin_at"], begin_at)
                                 if "begin_at" in inst_dict else begin_at)
        try:
            prev = inst_dict["end_at"]
        except KeyError:
            inst_dict["end_at"] = end_at
        else:
            inst_dict["end_at"] = (
                max(prev, end_at) if prev
                else None)
        for rtype in instance_resources:
            seg = Segment(
                resource_id=inst_dict[rtype + "_id"].id,
                cost=getattr(inst1, rtype) * tariffs.get(rtype, 1),
                begin_at=begin_at,
                end_at=end_at)
            db.session.add(seg)

    for inst_dict in instance_infos.values():
        seg = Segment(
            resource_id=inst_dict["inst2"].id,
            cost=0,
            begin_at=inst_dict.get("begin_at", None),
            end_at=inst_dict.get("end_at", None))
        db.session.add(seg)

    db.session.commit()


if __name__ == "__main__":
    main()
