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

For Team-based projects, HTTP requests must have the trusted current Team on
the attribute configured by `PERMAFROST_CONTEXT_REQUEST_ATTR`. Role querysets,
permission changes, and membership changes are then limited to that Team.
Service calls should pass `context_object=team` when a request is unavailable.
Authenticated superusers retain access in every context.

See [Team Context Setup](team-context.md) for the complete middleware,
authorization-backend, and application-queryset pattern.

Permission changes go through `PermafrostRole` helper methods so required permissions are preserved. Service API calls reject permissions that are not allowed by the role category.

Unknown permission IDs and user IDs raise validation errors. This helps callers distinguish "not allowed for this role category" from "does not exist".

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

## Collection Queries

Role and membership collections use page-number pagination. The response shape
is:

```json
{
  "count": 125,
  "next": "https://example.test/api/permafrost/roles/?page=2",
  "previous": null,
  "results": []
}
```

Configure the defaults in Django settings:

```python
PERMAFROST_API_PAGE_SIZE = 50
PERMAFROST_API_MAX_PAGE_SIZE = 200
```

Clients may request a smaller page using `page_size`; requests above the
configured maximum are capped. Invalid pagination settings are reported by
Django system checks.

The role collection supports:

- `search`: case-insensitive search across name, slug, and description
- `category`: exact category key
- `locked`: `true`, `false`, `1`, or `0`
- `ordering`: comma-separated `name`, `slug`, `category`, `locked`, or `id`
- `page` and `page_size`: pagination controls

Prefix an ordering field with `-` for descending order:

```http
GET /api/permafrost/roles/?search=manager&category=staff&ordering=-name
```

The role-user collection supports:

- `search`: case-insensitive username and email search when those user-model fields exist
- `ordering`: comma-separated `id`, `username`, or `email`
- `page` and `page_size`: pagination controls

Membership ordering uses the custom user model's `USERNAME_FIELD` internally;
the public query parameter remains `username`.

## HTTP API Behavior

Role `category` is set when a role is created and cannot be changed through the update endpoints. This matches the built-in forms, where category controls the required and optional permission set.

Deleting a role through the HTTP API soft-deletes it by setting `deleted=True`. Locked roles and configured default roles are protected by the model/service behavior and are not marked deleted.

Permission updates require known permission IDs. Permissions that exist but are outside the role category's optional/required permission set return `400 Bad Request`; the update is not partially applied.

User membership updates require known user IDs. Removing a user ID that does not exist returns `404`.

## Example Requests

Create a role:

```http
POST /api/permafrost/roles/
Content-Type: application/json

{
  "name": "Account Manager",
  "description": "Can help manage account-level tasks.",
  "category": "staff",
  "permission_ids": [12, 13]
}
```

Replace optional permissions:

```http
PUT /api/permafrost/roles/account-manager/permissions/
Content-Type: application/json

{
  "permission_ids": [12, 13]
}
```

Add users to a role:

```http
POST /api/permafrost/roles/account-manager/users/
Content-Type: application/json

{
  "user_ids": [42, 43]
}
```

The HTTP API remains optional. Importing `permafrost`, running migrations, and using `permafrost.api.services` do not require DRF.
