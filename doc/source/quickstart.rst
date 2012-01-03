Quickstart
===========================

Install the package:

.. code-block:: shell

    # yum install nova-billing

Start the server:

.. code-block:: shell

    # /etc/init.d/nova-billing start

Now instance state changes will be stored to a database.

Try to run or terminate an instance and check that the daemon returns reports:

.. code-block:: shell

    $ curl http://localhost:8787/projects/systenant/2011 | python -mjson.tool

Its output should look like this:

.. code-block:: javascript

    {
        "period_end": "2012-01-01T00:00:00Z", 
        "period_start": "2011-01-01T00:00:00Z", 
        "project": {
            "instances": {
                "count": 7, 
                "usage": {
                    "local_gb_h": 68495.83333333333, 
                    "memory_mb_h": 7013973.333333333, 
                    "vcpus_h": 3424.7916666666665
                }
            }, 
            "name": "systenant", 
            "url": "http://127.0.0.1:8787/projects/systenant"
        }
    }
