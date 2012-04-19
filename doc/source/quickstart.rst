Quickstart
===========================

Install the package:

.. code-block:: bash

    # yum install nova-billing

Start the servers:

.. code-block:: bash

    # /etc/init.d/nova-billing-heart start
    # /etc/init.d/nova-billing-os-amqp start

Now instance state changes will be stored to a database.

Configure Glance to use `Nova Billing Glance Middleware <config.html#nova-billing-glance>`_ and restart glance-api:

.. code-block:: bash

    # /etc/init.d/glance-api restart

Try to run or terminate an instance or create or remove a glance image. Then you can check that the daemon returns reports
(replace ``999888777666`` with a valid Admin's token):

.. code-block:: bash

    $ curl http://localhost:8787/bill -H "X-Auth-Token: 999888777666" | python -mjson.tool

Its output should look like this:

.. code-block:: javascript

    {
        "bill": [
            {
                "id": 1, 
                "name": "1", 
                "resources": [
                    {
                        "cost": 0.0, 
                        "created_at": "2012-01-19T17:37:24.024440Z", 
                        "destroyed_at": null, 
                        "id": 46, 
                        "name": null, 
                        "parent_id": 45, 
                        "rtype": "local_gb"
                    }, 
                    {
                        "cost": 8434.1570370370373, 
                        "created_at": "2012-01-19T17:37:24.024440Z", 
                        "destroyed_at": null, 
                        "id": 47, 
                        "name": null, 
                        "parent_id": 45, 
                        "rtype": "memory_mb"
                    }, 
                    {
                        "cost": 16.472962962962963, 
                        "created_at": "2012-01-19T17:37:24.024440Z", 
                        "destroyed_at": null, 
                        "id": 48, 
                        "name": null, 
                        "parent_id": 45, 
                        "rtype": "vcpus"
                    }, 
                    {
                        "cost": 0.0, 
                        "created_at": "2012-01-19T17:37:24.024440Z", 
                        "destroyed_at": null, 
                        "id": 45, 
                        "name": "12", 
                        "parent_id": null, 
                        "rtype": "nova/instance"
                    },  
                    {
                        "cost": 72559316.557037041, 
                        "created_at": "2012-01-19T16:23:20.293482Z", 
                        "destroyed_at": null, 
                        "id": 75, 
                        "name": "22", 
                        "parent_id": null, 
                        "rtype": "glance/image"
                    }
                ]
            }
        ], 
        "period_end": "2012-05-01T00:00:00Z", 
        "period_start": "2012-04-01T00:00:00Z"
    }
