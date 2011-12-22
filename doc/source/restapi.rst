Nova Billing REST API
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

If user asks for month or day statistics for a particular project, statistics per instance will also be reported.

Note. Date and time is UTC only in order to avoid problems with timezones and daylight saving time.
So, it is stored, retrieved, and specified in queries as UTC.

Examples::

    $ curl http://localhost:8787/projects/systenant/2011 | python -mjson.tool
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
    $ curl http://localhost:8787/projects/systenant/2011/12 | python -mjson.tool
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
    $ curl http://localhost:8787/projects-all/2011/12 | python -mjson.tool
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
