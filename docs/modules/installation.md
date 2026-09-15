# Installation

## Requirements

Django Permafrost currently supports:

- Python 3.11+
- Django 5.2 through 6.1

Django 5.1 and older are not supported by the current package metadata.

## Install

Install from PyPI:

```shell
python -m pip install django-permafrost
```

For local development, install the package in editable mode with the test extras:

```shell
python -m pip install -e ".[test]"
```

To use the optional Django REST Framework HTTP API:

```shell
python -m pip install "django-permafrost[api]"
```

The project no longer uses a root `requirements.txt`. Runtime dependencies live in `pyproject.toml`, and optional groups are used for development, tests, and docs.

## Django Apps

Add Permafrost and the required Django contrib apps:

```python
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "permafrost",
]
```

Then run migrations:

```shell
python manage.py migrate
```

## Required Settings

Define the role categories your application allows clients to manage:

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

PERMAFROST_DEFAULT_ROLES = []
PERMAFROST_EXCLUDED_ROLES = []
```

Permissions are configured with Django permission natural keys:

```python
(codename, app_label, model)
```

This avoids coupling configuration to database primary keys.

## Context Model

Permafrost roles are scoped to a context object. The default is Django's `Site` model:

```python
PERMAFROST_CONTEXT_MODEL = "sites.Site"
PERMAFROST_CONTEXT_REQUEST_ATTR = "site"
```

For organization or team based applications, configure the context model at the start of the project:

```python
PERMAFROST_CONTEXT_MODEL = "accounts.Organization"
PERMAFROST_CONTEXT_REQUEST_ATTR = "organization"
```

Permafrost will look for the current context object on the request using `PERMAFROST_CONTEXT_REQUEST_ATTR`. For example, middleware can attach `request.organization`.

If a request object is not available, the configured context model must have a default manager method named `get_current()`. The default `Site` integration uses `Site.objects.get_current()`.

Treat `PERMAFROST_CONTEXT_MODEL` like `AUTH_USER_MODEL`: set it before production data exists and avoid changing it later.

## Upgrade Notes

Existing projects that used the original Site-based behavior can keep the default settings. The migration backfills the new context fields from each role's `site`.

Projects moving to an organization or team context should plan a data migration that maps existing Site-scoped roles to the new context objects. Do not change `PERMAFROST_CONTEXT_MODEL` in a production project without a deliberate migration plan.
