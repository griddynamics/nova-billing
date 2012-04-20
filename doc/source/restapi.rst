REST API
===============================

.. contents:: 
  :depth: 2
  :local:

Overview
--------------

Nova Billing Heart supports the following requests:

* ``GET /version``;
* ``GET /bill``;
* ``POST /event``;
* ``GET /tariff`` and ``POST /tariff``;
* ``GET /resource`` and ``POST /resource``;
* ``GET /account``.

All these requests return JSON on success. Data for POST requests also must be JSON.
We use JSON schema (http://json-schema.org/) for format description.

Date and time are always UTC in order to avoid problems with timezones and daylight saving time.


Version
-------

``GET /version`` returns information about application name, version, and available URLs.

Bill
------
``GET /bill`` returns information about charged money for requested account on requested time period by resource.

Time period can be specified in two forms.

1. Start and end are given explicitly with ``period_start`` 
   and ``period_end`` request parameters.

2. ``time_period`` request parameter is used. It can be a year 
   (specified as ``year``), a month (``year-month``), or a day
   (``year-month-day``). All components are integers. Month and
   day numbers start with 1.

If period is omitted, the bill will be for the current month.

Account should be specified by its name with ``account`` argument. 

Billing report has the following schema:

.. code-block:: javascript

    {
        "type": "object", 
        "description": "Billing report", 
        "properties": {
            "period_start": {
                "required": true, 
                "type": "string", 
                "description": "The beginning of the requested period", 
                "format": "date-time"
            }, 
            "period_end": {
                "required": true, 
                "type": "string", 
                "description": "The end of the requested period", 
                "format": "date-time"
            },
            "bill": {
                "items": {
                    "type": "object", 
                    "description": "Array of account billing reports"
                }, 
                "required": true, 
                "type": "array"
            }
        }
    }

Account billing report has the following schema:

.. code-block:: javascript

    {
        "type": "object", 
        "description": "Account billing report", 
        "properties": {
            "id": {
                "required": true, 
                "type": "integer", 
                "description": "Account ID"
            }, 
            "name": {
                "required": true, 
                "type": "string", 
                "description": "Account name"
            },
            "resources": {
                "items": {
                    "type": "object", 
                    "description": "Array of resource billing reports"
                }, 
                "required": true, 
                "type": "array"
            }
        }
    }

Resource billing report has the following schema:

.. code-block:: javascript

    {
        "type": "object", 
        "description": "Resource billing report", 
        "properties": {
            "id": {
                "required": true, 
                "type": "integer", 
                "description": "Resource ID"
            }, 
            "rtype": {
                "required": true, 
                "type": "string", 
                "description": "Resource type"
            }, 
            "name": {
                "required": true, 
                "type": [
                    "string", 
                    "null"
                ], 
                "description": "Resource name or null if none"
            },
            "parent_id": {
                "required": true, 
                "type": [
                    "string", 
                    "null"
                ], 
                "description": "ID of resource parent or null if none"
            },
            "created_at": {
                "required": true, 
                "type": "string", 
                "description": "Date of object creation", 
                "format": "date-time"
            }, 
            "destroyed_at": {
                "required": true, 
                "type": [
                    "string", 
                    "null"
                ], 
                "description": "Date of object destruction (termination) or null if not destroyed", 
                "format": "date-time"
            }
            "cost": {
                "required": true, 
                "type": "number", 
                "description": "Billed money on the requested period"
            }, 
        }
    }

Example of billing report:

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


Examples of billing queries.

In these examples, ``999888777666`` is assumed to be a valid Admin's token.

Bill for account ``1`` on 2012 year:

.. code-block:: bash

    $ curl "http://localhost:8787/bill?account=1&time_period=2012" -H "X-Auth-Token: 999888777666"

Bill for all accounts on December, 2012:

.. code-block:: bash

    $ curl "http://localhost:8787/bill?time_period=2012-12" -H "X-Auth-Token: 999888777666"

Bill for account ``2`` from ``2012-01-01 00:00:00`` till ``2012-01-01 01:00:00``:

.. code-block:: bash

    $ curl "http://localhost:8787/bill?account=2&period_start=2012-01-01T00%3A00%3A00Z&period_end=2012-01-01T01%3A00%3A00Z" -H "X-Auth-Token: 999888777666"

    
Event
-----

``POST /event`` notifies the Heart about a new event.
All appropriate resources and accounts will be created lazily, so, there is no need to create a resource before posting an event.

Request data has the following schema:

.. code-block:: javascript

    {
        "type": "object", 
        "description": "Resource event", 
        "properties": {
            "account": {
                "required": false, 
                "type": "integer", 
                "description": "Account name"
            }, 
            "datetime": {
                "required": true, 
                "type": "string", 
                "description": "Event datatime", 
                "format": "date-time"
            },            
            "name": {
                "required": false, 
                "type": "string", 
                "description": "Resource name"
            },
            "rtype": {
                "required": true, 
                "type": "string", 
                "description": "Resource type"
            },
            "attrs": {
                "required": false, 
                "type": "object",
                "description": "Dictionary of resource attributes that should be set"
            },
            "linear": {
                "required": true, 
                "type": "number", 
                "description": "Linear price for the resource"
            },
            "fixed": {
                "required": true, 
                "type": ["number", "null"], 
                "description": "Fixed price for the resource or null to stop charging"
            },
            "children": {
                "items": {
                    "type": "object", 
                    "description": "Array of events of child resources"
                }, 
                "required": false, 
                "type": "array"
            }
        }
    }

``account`` and ``datatime`` should be present for the root resource event. They are ignored for all child resources.
``account`` can be omitted for the root resource event if the resource is already created.

``linear`` and ``fixed`` attributes control charging schemas for resources. They are mutually exclusive. 

* For fixed schema, charged money is the product of resource type tariff and the provided ``fixed`` value.
* For linear schema, charged money is the product of resource type tariff, the provided ``linear`` value, and
  period length in years.

If no tariff is stored for the given resource type, it will be assumed to be 1.


Request data example:

.. code-block:: javascript

    {
        "account": "2", 
        "name": 16, 
        "datetime": "2011-01-02T00:00:00Z", 
        "attrs": {
            "instance_type": "m1.small"
        }, 
        "fixed": 0, 
        "rtype": "nova/instance", 
        "children": [
            {
                "rtype": "local_gb", 
                "linear": 20
            }, 
            {
                "rtype": "memory_mb", 
                "linear": 2048
            }, 
            {
                "rtype": "vcpus", 
                "linear": 1
            }
        ]
    }

Here a virtual machine instance will be charged. Its disk, RAM, and CPU will be charged after linear scheme.
Its instance type is ``m1.small`` (this attribute can be retrieved with ``GET /resource`` call).


Tariff
------
Tariffs can be retrieved with ``GET /tariff`` and set with ``POST /tariff``. Tariff name equals to the corresponding resource type.

Setting request data has the following schema:

.. code-block:: javascript

    {
        "type": "object", 
        "properties": {
            "datetime": {
                "required": true, 
                "type": "string", 
                "description": "Since that datatime tariffs are changed", 
                "format": "date-time"
            },            
            "migrate": {
                "required": false, 
                "type": "boolean", 
                "description": "Whether all currently charging resources should migrate to the new tariffs"
            },
            "values": {
                "required": false, 
                "type": "object",
                "description": "Dictionary of the new tariffs"
            }
        }
    }

Setting tariff example:
 
.. code-block:: javascript

    {
        "datetime": "2010-01-01T00:00:00.000000Z",
        "migrate": false,
        "values": {
            "local_gb": 2.0,
            "memory_mb": 3.0,
            "vcpus": 0.5,
            "glance/image": 1.0
        }
    }

Response to ``GET /tariff`` is a tariff dictionary and looks like this:

.. code-block:: javascript

    {
        "local_gb": 2.0,
        "memory_mb": 3.0,
        "vcpus": 0.5,
        "glance/image": 1.0
    }

Resource
--------

Resources can be retrieved with ``GET /resource`` and set with ``POST /resource``.

Setting request data schema is nearly the same as post event schema.
The difference is that ``datetime``, ``linear``, and ``fixed`` attributes
are not used. 

Response to ``GET /resource`` is an array of resource objects and looks like this:

.. code-block:: javascript

    [
        {
            "account_id": 1, 
            "rtype": "nova/instance", 
            "parent_id": null, 
            "attrs": {
                "instance_type": "m1.small"
            }, 
            "id": 1, 
            "name": "16"
        }, 
        {
            "account_id": 1, 
            "rtype": "local_gb", 
            "parent_id": 1, 
            "attrs": {}, 
            "id": 2, 
            "name": null
        }, 
        {
            "account_id": 1, 
            "rtype": "memory_mb", 
            "parent_id": 1, 
            "attrs": {}, 
            "id": 3, 
            "name": null
        }, 
        {
            "account_id": 1, 
            "rtype": "vcpus", 
            "parent_id": 1, 
            "attrs": {}, 
            "id": 4, 
            "name": null
        }
    ]
    
Account
-------

Resources can be retrieved with ``GET /account``.

Response is an array of account objects and looks like this:

.. code-block:: javascript

    [
        {
            "id": 1, 
            "name": "4"
        }
        {
            "id": 2, 
            "name": "35"
        }
    ]
