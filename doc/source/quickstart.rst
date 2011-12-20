Quickstart
===========================

Install the package::

    # yum install openstack-nova-billing

Start the server::

    # /etc/init.d/openstack-nova-billing start

Now instance state changes will be stored to a database.

Try to run or terminate an instance and check that the daemon returns reports::

    $ curl http://localhost:8787/projects/systenant/2011 | python -mjson.tool


Its output should look like this::

    {
        "date": "2011-01-01T00:00:00Z",
        "duration": "year",
        "projects": {
            "systenant": {
                "instances_count": 2,
                "name": "systenant",
                "usage": {
                    "local_gb": 12,
                    "memory_mb": 45,
                    "vcpus": 39
                },
                "running": 257115,
                "url": "http://127.0.0.1:8787/projects/systenant"
            }
        }
    }
