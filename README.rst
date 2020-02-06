Permafrost
==========

Permafrost is an extention to Django's Permissions framework.

It adds:
* A View Mixin that supports additional permissions for different methods types (GET, POST, PUT, etc) for extra granular control.
* A View Mixin that supports logging any failed permission checks to a log configured in Django.
* An App that supports Client defineable roles and permissions.  This uses the underlying Django Permission system and controls which permissions are exposed to the users.

Adds Client Definable Permissions to Django.
