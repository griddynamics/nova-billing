Configuration
=============

Nova Billing uses the same configuration file ``nova.conf`` as nova
daemons and utilities.

Nova Billing introduces the following options.

``billing_listen``
  IP address for Billing API to listen
  (string, ``"0.0.0.0"`` by default).

``billing_listen_port``
  Billing API port (integer, ``8787`` by default).

``billing_sql_connection``
  Connection string for billing sql database (string,
  ``"sqlite:////var/lib/nova/nova_billing.sqlite"`` by default).

The daemon uses the following options to connect to rabbit daemon:

* ``rabbit_host``;
* ``rabbit_port``;
* ``rabbit_userid``;
* ``rabbit_password``;
* ``rabbit_virtual_host``.
  
The daemon saves logs to ``nova-billing.log`` file in nova logs
directory (e.g., ``/var/log/nova/``).
