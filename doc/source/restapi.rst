OpenStack Nova Billing REST API
===============================

Nova billing daemon supports two forms of requests.

#. ``/projects/{project}/{time period}``.
#. ``/projects-all/{time period}``.

The first form retrieves statistics for the given project.
The second form retrieves data for all projects.

Each form has three variants.

#. Report for a year: ``/projects/{project}/{year}`` and ``/projects-all/{year}``.
#. Report for a month: ``/projects/{project}/{year}/{month}`` and ``/projects-all/{year}/{month}``.
#. Report for a day: ``/projects/{project}/{year}/{month}/{day}`` and ``/projects-all/{year}/{month}/{day}``.

``month`` is an integer between 1 (January) and 12 (December).

``day`` is an integer between 1 and the number of days in the given month and year.

Note. Date and time is UTC only in order to avoid problems with timezones and daylight saving time.
So, it is stored, retrieved, and specified in queries as UTC.

Examples::

    $ curl http://localhost:8787/projects/systenant/2011 | python -mjson.tool
    {
        "date": "2011-01-01T00:00:00Z", 
        "duration": "year", 
        "projects": {
            "systenant": {
                "instances_count": 2, 
                "name": "systenant", 
                "running": 329560, 
                "url": "http://127.0.0.1:8787/projects/systenant", 
                "usage": {
                    "local_gb": 6591200, 
                    "memory_mb": 674938880, 
                    "vcpus": 329560
                }
            }
        }
    }
    $ curl http://localhost:8787/projects/systenant/2011/12 | python -mjson.tool
    {
        "date": "2011-12-01T00:00:00Z", 
        "duration": "month", 
        "projects": {
            "systenant": {
                "instances": {
                    "55": {
                        "created_at": "2011-12-15T18:22:33.887135Z", 
                        "destroyed_at": null, 
                        "id": 55, 
                        "running": 327822, 
                        "usage": {
                            "local_gb": 6556440, 
                            "memory_mb": 671379456, 
                            "vcpus": 327822
                        }
                    }, 
                    "56": {
                        "created_at": "2011-12-15T18:23:06.452062Z", 
                        "destroyed_at": "2011-12-15T18:52:05.391688Z", 
                        "id": 56, 
                        "running": 1738, 
                        "usage": {
                            "local_gb": 34760, 
                            "memory_mb": 3559424, 
                            "vcpus": 1738
                        }
                    }
                }, 
                "instances_count": 2, 
                "name": "systenant", 
                "running": 329560, 
                "url": "http://127.0.0.1:8787/projects/systenant", 
                "usage": {
                    "local_gb": 6591200, 
                    "memory_mb": 674938880, 
                    "vcpus": 329560
                }
            }
        }
    }
    $ curl http://localhost:8787/projects-all/2011/12 | python -mjson.tool
    {
        "date": "2011-12-01T00:00:00Z", 
        "duration": "month", 
        "projects": {
            "systenant": {
                "instances": {
                    "55": {
                        "created_at": "2011-12-15T18:22:33.887135Z", 
                        "destroyed_at": null, 
                        "id": 55, 
                        "running": 327822, 
                        "usage": {
                            "local_gb": 6556440, 
                            "memory_mb": 671379456, 
                            "vcpus": 327822
                        }
                    }, 
                    "56": {
                        "created_at": "2011-12-15T18:23:06.452062Z", 
                        "destroyed_at": "2011-12-15T18:52:05.391688Z", 
                        "id": 56, 
                        "running": 1738, 
                        "usage": {
                            "local_gb": 34760, 
                            "memory_mb": 3559424, 
                            "vcpus": 1738
                        }
                    }
                }, 
                "instances_count": 2, 
                "name": "systenant", 
                "running": 329560, 
                "url": "http://127.0.0.1:8787/projects/systenant", 
                "usage": {
                    "local_gb": 6591200, 
                    "memory_mb": 674938880, 
                    "vcpus": 329560
                }
            }
        }
    }
