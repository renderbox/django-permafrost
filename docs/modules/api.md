# API

Permafrost exposes two API layers:

- a Python service API that does not require Django REST Framework
- an optional DRF HTTP API for projects that install DRF

## Python Service API

Use `permafrost.api.services` when application code needs to work with roles directly.

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

Useful service functions include:

- `list_roles`
- `get_role`
- `create_role`
- `update_role`
- `delete_role`
- `list_categories`
- `set_role_permissions`
- `add_role_permissions`
- `remove_role_permissions`
- `list_role_permissions`
- `add_role_users`
- `remove_role_users`
- `list_role_users`

The service API uses the same context helpers as the built-in views. Pass `context_object` explicitly, pass a `request`, or let the configured context model resolve the current object.

Permission changes go through `PermafrostRole` helper methods so required permissions are preserved and disallowed permissions are ignored.

## Optional DRF HTTP API

Install the optional API extra:

```shell
python -m pip install "django-permafrost[api]"
```

Then include the API URLconf:

```python
from django.urls import include, path

urlpatterns = [
    path("api/permafrost/", include("permafrost.api.urls")),
]
```

The included routes expose:

- `GET /roles/`
- `POST /roles/`
- `GET /roles/{slug}/`
- `PUT /roles/{slug}/`
- `PATCH /roles/{slug}/`
- `DELETE /roles/{slug}/`
- `GET /roles/categories/`
- `GET /roles/{slug}/permissions/`
- `PUT /roles/{slug}/permissions/`
- `GET /roles/{slug}/users/`
- `POST /roles/{slug}/users/`
- `DELETE /roles/{slug}/users/{user_id}/`

The HTTP API remains optional. Importing `permafrost`, running migrations, and using `permafrost.api.services` do not require DRF.
