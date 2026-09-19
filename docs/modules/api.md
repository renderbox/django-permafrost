# API

Permafrost exposes two API layers:

- a Python service API that does not require Django REST Framework
- an optional DRF HTTP API with an OpenAPI schema

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

Configure drf-spectacular as DRF's schema class. Keep any existing REST
framework settings alongside this entry:

```python
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
```

Then include the API URLconf:

```python
from django.urls import include, path

urlpatterns = [
    path("api/permafrost/", include("permafrost.api.urls")),
]
```

The HTTP API requires an explicit URL version. With the mounting point above,
version 1 begins at `/api/permafrost/v1/`; unversioned routes are not exposed.
See [API Versioning](api-versioning.md) for the compatibility and deprecation
policy.

Version 1 exposes:

- `GET /schema/`
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
- `DELETE /roles/{slug}/users/`
- `DELETE /roles/{slug}/users/{user_id}/`

## OpenAPI Schema

The public OpenAPI 3.0 schema is available from the versioned API root:

```http
GET /api/permafrost/v1/schema/
Accept: application/vnd.oai.openapi+json
```

The endpoint returns YAML by default. Request JSON through content negotiation
or with `?format=json`:

```http
GET /api/permafrost/v1/schema/?format=json
```

The document includes request and response components, pagination and query
parameters, stable operation IDs, validation responses, and examples for role,
permission, category, and membership workflows. Schema paths are relative to a
`servers` entry derived from the project's actual URL mounting point, so the
document remains accurate when the package is included under a different
prefix.

The schema endpoint intentionally permits anonymous reads. Application data
endpoints continue to use `PermafrostAPIPermission` and the project's DRF
authentication configuration.

## Collection Queries

Role and membership collections use page-number pagination. The response shape
is:

```json
{
  "count": 125,
  "next": "https://example.test/api/permafrost/v1/roles/?page=2",
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
GET /api/permafrost/v1/roles/?search=manager&category=staff&ordering=-name
```

The role-user collection supports:

- `search`: case-insensitive username and email search when those user-model fields exist
- `ordering`: comma-separated `id`, `username`, or `email`
- `page` and `page_size`: pagination controls

Membership ordering uses the custom user model's `USERNAME_FIELD` internally;
the public query parameter remains `username`.

## Membership Identifiers

Membership mutations use primary keys by default. Projects may opt into one
additional stable identifier by configuring a field on their custom user
model:

```python
PERMAFROST_API_USER_LOOKUP_FIELD = "username"
```

The configured field can be `username`, a unique email field, or a
project-defined field such as `external_id`. It must be a concrete model field
declared with `unique=True`. Permafrost reports missing, non-concrete, and
non-unique fields through Django system checks. Email lookup should only be
enabled when the user model enforces unique email addresses.

After configuration, add or remove memberships using exact identifier values:

```http
POST /api/permafrost/v1/roles/account-manager/users/
Content-Type: application/json

{
  "user_identifiers": ["grant", "devon"]
}
```

```http
DELETE /api/permafrost/v1/roles/account-manager/users/
Content-Type: application/json

{
  "user_identifiers": ["grant"]
}
```

The collection `POST` and `DELETE` endpoints accept exactly one of
`user_ids` or `user_identifiers`. Every submitted user must exist before any
membership is changed. The original
`DELETE /roles/{slug}/users/{user_id}/` endpoint remains available for
single-user primary-key removal.

## HTTP API Behavior

Role `category` is set when a role is created and cannot be changed through the update endpoints. This matches the built-in forms, where category controls the required and optional permission set.

Deleting a role through the HTTP API soft-deletes it by setting `deleted=True`. Locked roles and configured default roles are protected by the model/service behavior and are not marked deleted.

Permission updates require known permission IDs. Permissions that exist but are outside the role category's optional/required permission set return `400 Bad Request`; the update is not partially applied.

User membership updates require every submitted ID or configured identifier to
resolve. Bulk additions and removals return `400 Bad Request` without making a
partial change when a value is unknown. Removing a single user through the
primary-key URL returns `404` when that user does not exist.

## Example Requests

Create a role:

```http
POST /api/permafrost/v1/roles/
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
PUT /api/permafrost/v1/roles/account-manager/permissions/
Content-Type: application/json

{
  "permission_ids": [12, 13]
}
```

Add users to a role:

```http
POST /api/permafrost/v1/roles/account-manager/users/
Content-Type: application/json

{
  "user_ids": [42, 43]
}
```

The HTTP API remains optional. Importing `permafrost`, running migrations, and
using `permafrost.api.services` do not require DRF or drf-spectacular.
