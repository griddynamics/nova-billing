What's new
==========

Nova Billing v1 was a small, fast, and reliable application that stored billing
information about instances and images and generated reports on resource usage.
Its main fault was monolithic inflexible architecture. Adding a new resource type
(for example, local volume) leaded to changes in API and data model.

Nova Billing v2 is a totally new solution. Its API and architecture were rewritten
from scratch. The new Nova Billing introduces extensible modularized system with separate components.

Nova Billing v2 can charge arbitrary resources according to custom billing schemas
and, naturally, with different tariffs.

Nova Billing v2 does not depend on any UI for OpenStack Cloud (neither OpenStack Dashboard
nor any other solution). It does not require a particular OpenStack release. Provided
components allow integration with diablo and essex and this list can be extended.

Nova Billing v2 is event-driven and does not consumes system resources for periodical
polling.

Nova Billing v2 uses a RESTful protocol, so it is easy to integrate it with miscellaneous 
user clients and to add third-party components notifying about arbitrary events.
