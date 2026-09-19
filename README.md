![Python Tests (Develop)](https://github.com/renderbox/django-permafrost/actions/workflows/python-test.yml/badge.svg)

![Python Tests (Master)](https://github.com/renderbox/django-permafrost/actions/workflows/python-test-master.yml/badge.svg)

# Django Permafrost

Django Permafrost is an extension to Django's permissions framework. Its goal is to allow developers to expose selected permissions to client users so they can create and manage custom user roles inside a tenant or site context.

It adds:

- A View Mixin that supports user permissions based on different HTTP method types (GET, POST, PUT, etc) for extra granular control.
- A View Mixin that captures into Django's logging setup any failed permission checks.
- An app that supports client user definable roles and permissions. This uses Django's underlying permission system and controls which permissions are exposed to users.
  - Developers can define required permissions for each role category and optional permissions that can be selected by the client.

For example, a SaaS platform may allow client administrators to manage other users in their account. They may want one employee to manage email lists but not invite users, while another employee can do both. Permafrost lets the developer define the permission boundaries and lets the client assemble roles inside those boundaries.

## Supported versions

This release targets:

- Python 3.11+
- Django 5.2 through Django 6.1

Django 5.1 and older are no longer supported.

## Installation

To install, use pip:

```shell
python -m pip install django-permafrost
```

To add it to your project, add it to the list of installed apps in your `settings.py`:

```python

INSTALLED_APPS = [
    ...
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sites",
    "permafrost",
    ...
]
```

Then migrate:

```shell
python manage.py migrate
```

## Setup

The goal of Django Permafrost is to allow clients to create their own Permafrost roles under developer-defined categories with developer-defined required and optional permissions.

An example developer-defined category looks like this:

```python
from django.utils.translation import gettext_lazy as _

PERMAFROST_CATEGORIES = {
    "user": {
        "label": _("User"),
        "access_level": 1,
        "optional": [
            {
                "label": _("Can Add Users to Role"),
                "permission": ("add_user_to_role", "permafrost", "permafrostrole"),
            },
        ],
        "required": [
            {
                "label": _("Can add Role"),
                "permission": ("add_permafrostrole", "permafrost", "permafrostrole"),
            },
        ],
    },
}
```

This would be added to your Django `settings.py` file (or, at least, included into).

In the above, we define the User category, give it the localizable label of "User", and provide two permissions in Django's natural key format. Primary keys can differ between environments, so natural keys are safer for permission configuration.

There is also an access_level setting to help make sorting access levels more easily.

### Context model

Permafrost roles are scoped to a context object. By default, that context is Django's `Site` model, which preserves the original subdomain/site-per-client behavior:

```python
PERMAFROST_CONTEXT_MODEL = "sites.Site"
PERMAFROST_CONTEXT_REQUEST_ATTR = "site"
```

Projects that use a different tenant model can set the context model once at the beginning of the project, similar to how a custom user model is configured:

```python
PERMAFROST_CONTEXT_MODEL = "accounts.Organization"
PERMAFROST_CONTEXT_REQUEST_ATTR = "organization"
```

Permafrost expects the current context object to be available on the request using `PERMAFROST_CONTEXT_REQUEST_ATTR`. For example, middleware might attach `request.organization`. If no request context is available, the configured context model must provide a manager method named `get_current()`. The built-in `Site` default uses `Site.objects.get_current()`.

Internally, Permafrost stores the context through Django's content type framework, but each project should configure exactly one context model for the lifetime of that project.

For more detail, see the files in `docs/modules/`, especially `installation.md` and `models.md`.

The complete Team setup guide covers middleware, authentication backends,
role assignment, request-aware checks, queryset scoping, cross-Team isolation,
and superuser behavior: [`docs/modules/team-context.md`](docs/modules/team-context.md).

## Recommendations

It is recommended that you update your code to use `PermafrostRole`'s built-in functions to add users and permissions. They add an extra level of checking to make sure the permissions passed in are allowed by the `PERMAFROST_CATEGORIES` configuration.

For example, permissions on a Group:

```python
group.permissions.set([permission_list])
group.permissions.add(permission, permission, ...)
group.permissions.remove(permission, permission, ...)
group.permissions.clear()
```

Can be replaced with:

```python
PermafrostRole.permissions_set([permission_list])
PermafrostRole.permissions_add(permission, permission, ...)
PermafrostRole.permissions_remove(permission, permission, ...)
PermafrostRole.permissions_clear()
```

## Convenience tools

There is a tool to help the developer list out the permissions available in the format permafrost expects.

```shell
> ./manage permlist
```

using the command will produce a list like this

```shell
> ./manage.py permlist

Permlist formatted for your PermafrostRoles configuration
{'label':_('Can add email address'), 'permission': ('add_emailaddress', 'account', 'emailaddress')},
{'label':_('Can change email address'), 'permission': ('change_emailaddress', 'account', 'emailaddress')},
{'label':_('Can delete email address'), 'permission': ('delete_emailaddress', 'account', 'emailaddress')},
...
```

Each line can be copied into the PERMAFROST_CATEGORIES config in the correct format.

## Python and HTTP APIs

Permafrost includes a DRF-independent service API:

```python
from permafrost.api import services

role = services.create_role(
    name="Account Manager",
    category="staff",
    context_object=organization,
)
services.set_role_permissions(role, permissions)
services.add_role_users(role, [user])
```

The HTTP API is built with Django REST Framework and remains optional. Install the API extra to use it:

```shell
python -m pip install "django-permafrost[api]"
```

Configure the schema backend in Django settings:

```python
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
```

Then include the API URLs:

```python
from django.urls import include, path

urlpatterns = [
    path("api/permafrost/", include("permafrost.api.urls")),
]
```

The version 1 endpoints are then available below `/api/permafrost/v1/`.
Unversioned HTTP routes are not exposed. See the
[API documentation](docs/modules/api.md) and
[versioning policy](docs/modules/api-versioning.md) for the supported contract.
The OpenAPI schema is available at `/api/permafrost/v1/schema/`.

## Authors and contributors

- Grant Viklund, principal author and maintainer
- Devon Jackson, contributor
