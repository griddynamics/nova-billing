Configuration
=============

Configuration parameters
------------------------

Nova Billing components read configuration from the ``/etc/nova-billing/settings.json``.
Here are acceptable keys.

``admin_token``
  admin token for interaction with Keystone.
  
``keystone_url``
  Keystone Admin URL.
  
``nova_url``
  Nova API URL.

``heart_db_url``
  Heart database URL.
    
``host`` and ``port``
  Host and port for Heart REST API.

``rabbit_host``,  ``rabbit_port``, ``rabbit_userid``, ``rabbit_password``, and ``rabbit_virtual_host``
  Parameters of Nova RabbitMQ daemon. These parameters are loaded from ``/etc/nova/nova.conf`` by default.

  
Nova Billing Glance
---------------------

Nova Billing Glance is a middleware. To integrate it with Glance, append these lines to your ``/etc/glance/glance-api.conf``:

::

    [filter:billing]
    paste.filter_factory = nova_billing.os_glance:GlanceBillingFilter.factory


and mention this filter in ``glance-api`` pipeline:

::

    [pipeline:glance-api]
    pipeline = versionnegotiation authtoken auth-context billing apiv1app
  