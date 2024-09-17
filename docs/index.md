# Welcome to Django Permafrost's documentation!

Getting at permissions just below the surface.

Django Permafrost adds a couple extra pieces of utility to Django's permission system.

1. It adds a View Mixin (PermafrostMixin) for views to add permissions at the HTML Method level (get, post, patch, put, delete, etc...).

2. It adds a View Mixin (PermafrostLogMixin) for logging failed login attempts that use the Permission View Mixin.

3. It adds a PermafrostRole model for creating permissions that can be controlled by a Client for other users on the site. It relies on and manages Django's built-in permission with groups.
