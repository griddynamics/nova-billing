REST API
===============================

Request format
--------------

Nova Billing daemon supports the following forms of requests.

1. ``GET /`` - report on available URLs and application name and version.

2. ``GET /projects`` and ``GET /projects-all`` - statistics for all
   projects.  Time period should be specified with ``period_start`` 
   and ``period_end`` request parameters. If they are omitted, current month is assumed.

3. ``GET /projects/{project}`` - statistics for requested
   ``{project}``. Time period is determined as described in previous item.

4. ``GET /projects-all/{time_period}`` - statistics for all
   projects on requested ``{time_period}`` (see below).

5. ``GET /projects/{project}/{time_period}`` - statistics for requested
   ``{project}`` on requested ``{time_period}`` (see below).

``{project}`` is a name of a project. It is not a project ID.

``{time_period}`` has three forms.

#. A year: ``GET /projects/{project}/{year}`` and ``GET /projects-all/{year}``.
#. A month: ``GET /projects/{project}/{year}/{month}`` and ``GET /projects-all/{year}/{month}``.
#. A day: ``GET /projects/{project}/{year}/{month}/{day}`` and ``GET /projects-all/{year}/{month}/{day}``.

``{time_period}`` components must follow the following rules.

1. ``{year}`` is an integer. It must contain exactly four decimal digits.

2. ``{month}`` is an integer between 1 (January) and 12 (December).

3. ``{day}`` is an integer between 1 and the number of days in the given
   month and year.

4. Both ``{month}`` and ``{day}`` must contain exactly 1 or 2 decimal digits,
   and the leading zero can be omitted.

Date and time always is UTC in order to avoid problems with timezones and daylight saving time.
So, ``{time_period}`` must be in UTC, and current month is also UTC.

An additional request parameter ``include`` is used to specify what statistics should be returned.
This parameter is one or two comma-separated items from the following list:

* ``instances`` or ``instances-long`` - short or long statistics for instances;
* ``images`` or ``images-long`` - short or long statistics for images.

Short form contains only summary for project, long statistics has additional information about individual instances or images.

Statistics for both instances and images can be retrieved by giving two comma-separated items, i.e. ``include=instances-long,images``.

If ``include`` parameter is omitted, statistics for instances will be returned.
It will be in short form for time period greater than 31 day and in long form otherwise.


Report format
-------------

All reports of Nova Billing daemon are in JSON. We use JSON schema (http://json-schema.org/) for format description.

For ``GET /`` request, report has the following schema:

.. code-block:: javascript

    {
        "type": "object", 
        "description": "Basic application information", 
        "properties": {
            "application": {
                "required": true, 
                "type": "string", 
                "description": "Application name"
            }, 
            "version": {
                "required": true, 
                "type": "string", 
                "description": "Application version"
            }, 
            "urls": {
                "type": "object", 
                "description": "Available URLs", 
                "properties": {
                    "projects-all": {
                        "required": true, 
                        "type": "string", 
                        "description": "projects-all URL"
                    }, 
                    "projects": {
                        "required": true, 
                        "type": "string", 
                        "description": "projects URL"
                    }
                }
            }
        }
    }

For request on statistics, report has the following schema:

.. code-block:: javascript

    {
        "type": "object", 
        "description": "Resource usage report", 
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
            "projects": {
                "items": {
                    "type": "object", 
                    "description": "Project statistics"
                }, 
                "required": false, 
                "type": "array", 
                "description": "Statistics for all projects"
            }, 
            "project": {
                "required": false, 
                "type": "object", 
                "description": "Project statistics"
            }
        }
    }

``project`` key is available if a particular project is requested (i.e.,
``GET /projects/{project}/{time_period}`` or ``GET /projects/{project}``).
Otherwise, ``projects`` key is available (``GET /projects``, 
``GET /projects-all``, and ``GET /projects-all/{time_period}`` requests).

Project statistics object has the following schema:

.. code-block:: javascript

    {
        "type": "object", 
        "description": "Project statistics", 
        "properties": {
            "name": {
                "required": true, 
                "type": "string", 
                "description": "Project name"
            }, 
            "url": {
                "required": true, 
                "type": "string", 
                "description": "Project URL"
            }, 
            "instances": {
                "required": false, 
                "type": "object", 
                "description": "Project instances statistics"
            }, 
            "images": {
                "required": false, 
                "type": "object", 
                "description": "Project images statistics"
            }
        }
    }

Project instances and project images statistics objects have the following schema:

.. code-block:: javascript

    {
        "type": "object", 
        "description": "Project items statistics", 
        "properties": {
            "count": {
                "type": "integer", 
                "description": "Number of items count"
            }, 
            "items": {
                "items": {
                    "type": "object", 
                    "description": "Individual item statistics"
                },
                "type": "array", 
                "description": "Statistics for individual items"
                "required": false, 
            }, 
            "usage": {
                "required": true, 
                "type": "object", 
                "description": "Resource usage (sum for all items)"
            }
        }
    }


``items`` property is available for long form of statistics.

Individual item statistics object has the following schema:

.. code-block:: javascript

    {
        "type": "object", 
        "description": "Individual item statistics", 
        "properties": {
            "id": {
                "required": true, 
                "type": "integer", 
                "description": "ID of the object"
            }, 
            "name": {
                "required": true, 
                "type": [
                    "string", 
                    "null"
                ], 
                "description": "Name of the object or null if none"
            },
            "usage": {
                "required": true, 
                "type": "object", 
                "description": "Resource usage"
            }, 
            "created_at": {
                "required": true, 
                "type": "string", 
                "description": "Date of object creation", 
                "format": "date-time"
            }, 
            "lifetime_sec": {
                "required": true, 
                "type": "integer", 
                "description": "Time in seconds while the object was alive during the requested time period"
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
        }
    }

Resource usage object has the following schema:

.. code-block:: javascript

    {
        "type": "object", 
        "description": "Resource usage", 
        "properties": {
            "local_gb_h": {
                "required": false, 
                "type": "number", 
                "description": "Hard drive usage (GB * h)"
            }, 
            "vcpus_h": {
                "required": false, 
                "type": "number", 
                "description": "CPU usage (number of CPUs * h)"
            }, 
            "memory_mb_h": {
                "required": false, 
                "type": "number", 
                "description": "RAM usage (MB * h)"
            }
        }
    }

If a property of resource usage object is omitted, it means that its value is zero.


Examples
--------

Instances statistics for ``systenant`` project on 2011 year:

.. code-block:: javascript

    $ curl "http://localhost:8787/projects/systenant/2011" | python -mjson.tool
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


Instances statistics for all projects on December, 2011:

.. code-block:: javascript

    $ curl "http://localhost:8787/projects-all/2011/12" | python -mjson.tool
    {
        "period_end": "2012-01-01T00:00:00Z", 
        "period_start": "2011-12-01T00:00:00Z", 
        "projects": {
            "systenant": {
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
            }, 
            "tenant2": {
                "instances": {
                    "count": 0, 
                    "usage": {}
                }, 
                "name": "tenant2", 
                "url": "http://127.0.0.1:8787/projects/tenant2"
            }
        }
    }

Images statistics (long form) for projects tenant2 on from 2011-01-01 00:00:00 till 2012-01-01 01:00:00:

.. code-block:: javascript

    $ curl "http://localhost:8787/projects/tenant2?include=images-long&period_start=2011-01-01T00%3A00%3A00Z&period_end=2012-01-01T01%3A00%3A00Z" | python -mjson.tool
    {
        "period_end": "2012-01-01T00:00:00Z", 
        "period_start": "2011-01-01T01:00:00Z", 
        "project": {
            "images": {
                "count": 4, 
                "items": [
                    {
                        "created_at": "2011-12-28T16:25:21.852159Z", 
                        "destroyed_at": null, 
                        "id": 1, 
                        "lifetime_sec": 286478, 
                        "name": "SL61_ramdisk", 
                        "usage": {
                            "local_gb_h": 0.0011111111111111111
                        }
                    }, 
                    {
                        "created_at": "2011-12-28T16:25:22.615385Z", 
                        "destroyed_at": null, 
                        "id": 2, 
                        "lifetime_sec": 286477, 
                        "name": "SL61_kernel", 
                        "usage": {
                            "local_gb_h": 0.2875
                        }
                    }, 
                    {
                        "created_at": "2011-12-28T16:25:23.376856Z", 
                        "destroyed_at": null, 
                        "id": 3, 
                        "lifetime_sec": 286476, 
                        "name": "SL61", 
                        "usage": {
                            "local_gb_h": 16.071666666666665
                        }
                    }, 
                    {
                        "created_at": "2011-12-29T08:04:07.497591Z", 
                        "destroyed_at": null, 
                        "id": 4, 
                        "lifetime_sec": 230152, 
                        "name": "ramdisk2", 
                        "usage": {
                            "local_gb_h": 0.0008333333333333334
                        }
                    }
                ], 
                "usage": {
                    "local_gb_h": 16.36111111111111
                }
            }, 
            "name": "tenant2", 
            "url": "http://127.0.0.1:8787/projects/tenant2"
        }
    }
