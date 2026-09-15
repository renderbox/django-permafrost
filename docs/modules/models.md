# Models

## PermafrostRole

`PermafrostRole` represents a tenant-scoped role that manages a Django `Group`.

Important fields:

- `name`: display name for the role
- `slug`: generated from `name`
- `description`: optional short description
- `category`: one of the keys configured in `PERMAFROST_CATEGORIES`
- `site`: legacy/default Site relationship retained for compatibility
- `context_content_type` and `context_object_id`: configured role context
- `group`: the Django `Group` used for users and permissions
- `locked`: prevents client deletion for protected roles
- `deleted`: soft-delete flag used by the role views

## Context

By default, a role is scoped to the current Django `Site`.

New projects can choose another context model:

```python
PERMAFROST_CONTEXT_MODEL = "accounts.Organization"
PERMAFROST_CONTEXT_REQUEST_ATTR = "organization"
```

The current context object can be set explicitly:

```python
role.set_context(organization)
```

The built-in views resolve context from the request:

```python
request.organization
```

or, with the default configuration:

```python
request.site
```

If no request context is available, Permafrost calls `get_current()` on the configured context model's default manager.

## Group Names

For Site-based projects, group names keep the historical format:

```text
<site_pk>_<category>_<role_slug>
```

For custom context models, group names include the model label:

```text
<app_label>_<model_name>_<object_pk>_<category>_<role_slug>
```

This keeps group names distinct across different context models and tenant records.

## Permission Helpers

Use the role helper methods instead of mutating the group permissions directly:

```python
role.permissions_add(permission)
role.permissions_remove(permission)
role.permissions_set(permission_queryset)
role.permissions_clear()
```

These helpers enforce `PERMAFROST_CATEGORIES`:

- required permissions are preserved
- optional permissions can be added or removed
- permissions outside the configured category are ignored

Direct calls such as `role.group.permissions.set(...)` bypass those checks and should be avoided in application code.

## User Helpers

The role also wraps common group membership operations:

```python
role.users_add(user)
role.users_remove(user)
role.users_clear()
role.user_set()
```

These methods delegate to the attached Django group.

## Save and Delete Behavior

On save, `PermafrostRole`:

1. generates the slug from the role name
2. resolves the context if needed
3. creates or renames the matching Django group
4. conforms the group permissions to the configured category

On delete, the matching group is deleted by signal after the role is deleted. Locked and default roles are protected from deletion by the model delete method.
