.. Django Permafrost documentation master file, created by
   sphinx-quickstart on Mon Feb 10 17:09:34 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Django Permafrost's documentation!
=============================================

Getting at permissions just below the surface.

Django Permafrost adds a couple extra pieces of utility to Django's permission system.

1. It adds a View Mixin (PermafrostMixin) for views to add permissions at the HTML Method level (get, post, patch, put, delete, etc...).

2. It adds a View Mixin (PermafrostLogMixin) for logging failed login attempts that use the Permission View Mixin.

3. It adds a Permission type (PermafrostRESTPermission) for the Django REST Framework.

4. It adds a PermafrostRole model for creating permissions that can be controlled by a Client for other users on the site.  It relies on and manages Django's built-in permission with groups.


Updated docs are forthcoming...

.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
