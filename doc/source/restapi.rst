REST API
===============================

Request format
--------------

Nova Billing daemon supports the following forms of requests.

1. ``GET /`` - report on available URLs and application name and version.

2. ``GET /projects`` and ``GET /projects-all`` - statistics for all
   projects on current month.

3. ``GET /projects/{project}`` - statistics for requested
   ``{project}`` on current month.

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
            "instances_count": {
                "type": "integer", 
                "description": "Number of instances running on requested time period"
            }, 
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
                "items": {
                    "type": "object", 
                    "description": "Instance statistics"
                }, 
                "required": false, 
                "type": "array", 
                "description": "Statistics for instances running on requested time period"
            }, 
            "usage": {
                "required": true, 
                "type": "object", 
                "description": "Resource usage (sum for all instances)"
            }, 
            "running_sec": {
                "required": true, 
                "type": "integer", 
                "description": "Sum of running_sec for all instances"
            }
        }
    }

``instances`` key is available only if time period is month or day and a
particular project is requested (queries ``GET /projects/{project}``,
``GET /projects/{project}/{year}/{month}``, and
``GET /projects/{project}/{year}/{month}/{day}``).


Instance statistics object has the following schema:

.. code-block:: javascript

    {
        "type": "object", 
        "description": "Instance statistics", 
        "properties": {
            "instance_id": {
                "required": true, 
                "type": "integer", 
                "description": "Instance ID"
            }, 
            "usage": {
                "required": true, 
                "type": "object", 
                "description": "Resource usage"
            }, 
            "created_at": {
                "required": true, 
                "type": "string", 
                "description": "Date of instance creation", 
                "format": "date-time"
            }, 
            "running_sec": {
                "required": true, 
                "type": "integer", 
                "description": "Time in seconds while instance was running on requested time period"
            }, 
            "destroyed_at": {
                "required": true, 
                "type": [
                    "string", 
                    "null"
                ], 
                "description": "Date of instance destruction (termination)", 
                "format": "date-time"
            }
        }
    }

Date of instance destruction is ``null`` if the instance is still running.

Resource usage object has the following schema:

.. code-block:: javascript

    {
        "type": "object", 
        "description": "Resource usage", 
        "properties": {
            "local_gb_h": {
                "required": true, 
                "type": "number", 
                "description": "Hard drive usage (GB * h)"
            }, 
            "vcpus_h": {
                "required": true, 
                "type": "number", 
                "description": "CPU usage (number of CPUs * h)"
            }, 
            "memory_mb_h": {
                "required": true, 
                "type": "number", 
                "description": "RAM usage (MB * h)"
            }
        }
    }

Examples
--------

Statistics for ``systenant`` project on 2011 year:

.. code-block:: javascript

    $ curl "http://localhost:8787/projects/systenant/2011" | python -mjson.tool
    {
        "period_end": "2012-01-01T00:00:00Z", 
        "period_start": "2011-01-01T00:00:00Z", 
        "project": {
            "instances_count": 7, 
            "name": "systenant", 
            "running_sec": 926399, 
            "url": "http://127.0.0.1:8787/projects/systenant", 
            "usage": {
                "local_gb_h": 13560.144444444444, 
                "memory_mb_h": 1388558.7911111112, 
                "vcpus_h": 678.0072222222223
            }
        }
    }

Statistics for ``systenant`` project on December, 2011:

.. code-block:: javascript

    $ curl "http://localhost:8787/projects/systenant/2011/12" | python -mjson.tool
    {
        "period_end": "2012-01-01T00:00:00Z", 
        "period_start": "2011-12-01T00:00:00Z", 
        "project": {
            "instances": [
                {
                    "created_at": "2011-12-15T18:22:33.887135Z", 
                    "destroyed_at": "2011-12-20T15:00:05.943989Z", 
                    "instance_id": 55, 
                    "running_sec": 419852, 
                    "usage": {
                        "local_gb_h": 2332.511111111111, 
                        "memory_mb_h": 238849.13777777777, 
                        "vcpus_h": 116.62555555555555
                    }
                }, 
                {
                    "created_at": "2011-12-15T18:23:06.452062Z", 
                    "destroyed_at": "2011-12-15T18:52:05.391688Z", 
                    "instance_id": 56, 
                    "running_sec": 1738, 
                    "usage": {
                        "local_gb_h": 9.655555555555555, 
                        "memory_mb_h": 988.7288888888888, 
                        "vcpus_h": 0.48277777777777775
                    }
                }, 
                {
                    "created_at": "2011-12-20T10:51:55.133627Z", 
                    "destroyed_at": "2011-12-20T15:00:06.150415Z", 
                    "instance_id": 57, 
                    "running_sec": 14891, 
                    "usage": {
                        "local_gb_h": 330.9111111111111, 
                        "memory_mb_h": 33885.29777777778, 
                        "vcpus_h": 16.545555555555556
                    }
                }, 
                {
                    "created_at": "2011-12-20T11:06:47.248165Z", 
                    "destroyed_at": "2011-12-20T15:00:05.741222Z", 
                    "instance_id": 58, 
                    "running_sec": 13998, 
                    "usage": {
                        "local_gb_h": 311.06666666666666, 
                        "memory_mb_h": 31853.226666666666, 
                        "vcpus_h": 15.553333333333333
                    }
                }, 
                {
                    "created_at": "2011-12-20T15:00:26.935897Z", 
                    "destroyed_at": null, 
                    "instance_id": 59, 
                    "running_sec": 158737, 
                    "usage": {
                        "local_gb_h": 3527.488888888889, 
                        "memory_mb_h": 361214.8622222222, 
                        "vcpus_h": 176.37444444444444
                    }
                }, 
                {
                    "created_at": "2011-12-20T15:01:46.182289Z", 
                    "destroyed_at": null, 
                    "instance_id": 60, 
                    "running_sec": 158658, 
                    "usage": {
                        "local_gb_h": 3525.733333333333, 
                        "memory_mb_h": 361035.0933333333, 
                        "vcpus_h": 176.28666666666666
                    }
                }, 
                {
                    "created_at": "2011-12-20T15:03:59.334251Z", 
                    "destroyed_at": null, 
                    "instance_id": 61, 
                    "running_sec": 158525, 
                    "usage": {
                        "local_gb_h": 3522.777777777778, 
                        "memory_mb_h": 360732.44444444444, 
                        "vcpus_h": 176.13888888888889
                    }
                }
            ], 
            "instances_count": 7, 
            "name": "systenant", 
            "running_sec": 926399, 
            "url": "http://127.0.0.1:8787/projects/systenant", 
            "usage": {
                "local_gb_h": 13560.144444444444, 
                "memory_mb_h": 1388558.7911111112, 
                "vcpus_h": 678.0072222222223
            }
        }
    }

Statistics for all projects on December, 2011:

.. code-block:: javascript

    $ curl "http://localhost:8787/projects-all/2011/12" | python -mjson.tool
    {
        "period_end": "2012-01-01T00:00:00Z", 
        "period_start": "2011-12-01T00:00:00Z", 
        "projects": {
            "systenant": {
                "instances_count": 7, 
                "name": "systenant", 
                "running_sec": 926399, 
                "url": "http://127.0.0.1:8787/projects/systenant", 
                "usage": {
                    "local_gb_h": 13560.144444444444, 
                    "memory_mb_h": 1388558.7911111112, 
                    "vcpus_h": 678.0072222222223
                }
            }
        }
    }
