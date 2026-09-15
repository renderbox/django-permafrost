# Django Permafrost

Django Permafrost adds tenant-aware role management on top of Django's built-in auth permissions and groups.

It provides:

1. `PermafrostMixin`, a permission mixin that can require different permissions for different HTTP methods.
2. `PermafrostLogMixin`, a helper for logging failed permission checks.
3. `PermafrostRole`, a model that lets client or tenant administrators manage a curated set of role permissions without bypassing Django's permission system.

Permafrost is intended for multi-tenant Django applications where developers define the permission surface and users inside each tenant can assemble roles from that approved set.

## Current Support

- Python 3.11+
- Django 5.2 through 6.1
- Django's `auth`, `contenttypes`, and `sites` apps

The default tenant context is Django's `Site` model. New projects can configure another context model, such as an `Organization` or `Team`, by setting `PERMAFROST_CONTEXT_MODEL`.

## Topics

- `modules/installation.md`: installation, settings, and upgrade notes
- `modules/models.md`: role model behavior, permission mapping, and context scoping
- `modules/views.md`: included views and mixins
- `modules/about.md`: architecture and maintenance notes
