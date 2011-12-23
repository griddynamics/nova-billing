REST API
===============================

Request format
--------------

Nova Billing daemon supports the following forms of requests.

1. ``/`` - report on available URLs and application name and version.

2. ``/projects`` and ``/projects-all`` - statistics for all
   projects on current month.

3. ``/projects/{project}`` - statistics for requested
   ``project`` on current month.

4. ``/projects-all/{time period}`` - statistics for all
   projects on requested ``time period`` (see below).

5. ``/projects/{project}/{time period}`` - statistics for requested
   ``project`` on requested ``time period`` (see below).

``project`` is a name of a project, e.g., ``systenant``. It is not
project ID, e.g., ``1``.

``time period`` has three forms.

#. A year: ``/projects/{project}/{year}`` and ``/projects-all/{year}``.
#. A month: ``/projects/{project}/{year}/{month}`` and ``/projects-all/{year}/{month}``.
#. A day: ``/projects/{project}/{year}/{month}/{day}`` and ``/projects-all/{year}/{month}/{day}``.

``time period`` components must follow the following rules.

1. ``year`` is an integer. It must contain exactly four decimal digits.

2. ``month`` is an integer between 1 (January) and 12 (December).

3. ``day`` is an integer between 1 and the number of days in the given
   month and year.

4. Both ``month`` and ``day`` must contain exactly 1 or 2 decimal digits,
   and the leading zero can be omitted.

Date and time always is UTC in order to avoid problems with timezones and daylight saving time.
So, ``time period`` must be in UTC, and current month is also UTC.


Report format
-------------

All reports of Nova Billing daemon are in JSON.

For ``/`` request, report on available URLs and application name and
version is a JSON object with the following keys.

``application``
  application name (string), i.e. ``"nova-billing"``.

``version``
  application version (string), e.g., ``"0.0.2"``.

``urls``
  available URLs - an object with string keys:
    + ``projects-all``, e.g., ``"http://localhost:8787/projects-all"``,
    + ``projects``, e.g., ``"http://localhost:8787/projects"``.

For request on statistics, report is a JSON object with the following
keys.

``period_start``
  The beginning of the requested period (string),
  e.g., ``"2011-12-01T00:00:00Z"``.

``period_end``
  The end of the requested period (string),
  e.g., ``"2012-01-01T00:00:00Z"``.

``projects`` or ``project``
  Summ of ``running_sec`` (see below) for all
  instances of this project, in seconds (integer).

``usage``
  Summ of ``usage`` (see below) for all
  instances of this project, in seconds (object).

``instances_count``
  Number of instances of this project that run
  on reqested time period (integer).

``instances``
  An array of instance statistics objects for instances of
  this project that run on requested time period (array);
  this key is present only if time period is month or day and a
  particular project is requested (queries ``/projects/{project}``,
  ``/projects/{project}/{year}/{month}``, and
  ``/projects/{project}/{year}/{month}/{day}``).

Instance statistics object has the following keys.

``instance_id``
  ID of instance (integer), e.g., ``55``.

``created_at``
  Date of instance creation (string),
  e.g., ``"2011-12-15T18:22:33.887135Z"``.

``destroyed_at``
  Date of instance destruction (termination)
  (string) or ``null`` if the instance is still running,
  e.g., ``"2011-12-20T15:00:05.943989Z"``.

``running_sec``
  Time in seconds while instance was running on
  requested time period (integer).

``usage``
  Resource usage (object) stored the following keys.

  ``local_gb_h``
    Hard drive usage (GB * h) (float).

  ``memory_mb_h``
    RAM usage (MB * h) (float).

  ``vcpus_h``
    CPU usage (number of CPUs * h) (float).

Date and time is always represented as a string in ISO 8601 format
``YYYY-MM-DDThh:mm:ss[.mmm]Z``, where ``Z`` indicates UTC time.

Examples
--------

Statistics for ``systenant`` project on 2011 year::

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

Statistics for ``systenant`` project on December, 2011::

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

Statistics for all projects on December, 2011::

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
