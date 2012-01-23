Quickstart
===========================

Install the package:

.. code-block:: bash

    # yum install nova-billing

Start the server:

.. code-block:: bash

    # /etc/init.d/nova-billing start

Now instance state changes will be stored to a database.

Try to run or terminate an instance and check that the daemon returns reports
(replace ``999888777666`` with a valid Admin's token):

.. code-block:: bash

    $ curl http://localhost:8787/projects -H "X-Auth-Token: 999888777666" | python -mjson.tool

Its output should look like this:

.. code-block:: javascript

    {
        "period_end": "2012-02-01T00:00:00Z", 
        "period_start": "2012-01-01T00:00:00Z", 
        "projects": [
            {
                "instances": {
                    "count": 7, 
                    "usage": {
                        "local_gb_h": 68495.83333333333, 
                        "memory_mb_h": 7013973.333333333, 
                        "vcpus_h": 3424.7916666666665
                    }
                }, 
                "id": "1", 
                "name": "systenant",
                "url": "http://127.0.0.1:8787/projects/systenant"
            }
        ]
    }
