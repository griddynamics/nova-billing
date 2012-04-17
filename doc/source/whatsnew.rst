What's new
==========

Nova Billing v1 was a small, fast, and reliable application that stored billing
information about instances and images and generated reports on resource usage.
Its main fault was monolithic inflexible architecture. Adding a new resource type
(for example, local volume) leaded to changes in API and database.

Nova Billing v2 is a totally new solution. Its API and architecture were rewritten
from scratch. The new Nova Billing introduces extensible modularized system with separate components.

Nova Billing v2 can charge arbitrary resources according to custom billing schemas
and, naturally, with different tariffs.
