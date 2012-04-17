Glossary
========

Resource
  Any object that can be added to a bill (i.e. an image). It must have a type (``nova/instance``, ``glance/image``)
  and, optionally, a name. A resource can consist of several resources (i.e. an instance consists of disk, RAM, and CPU).
  A resource can have a set of arbitrary attributes that should be interpreted by user agents.  

Account
  A tenant that owns resources and therefore can be charged.

Event
  An incident that influences some billed resources, i.e. instance creation or image destruction.

Tariff
  A rate for billing purposes.
