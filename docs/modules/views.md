# Views

## Mixins

### PermafrostMixin

`PermafrostMixin` extends Django's `PermissionRequiredMixin`.

It supports the normal `permission_required` attribute and also allows method-specific permissions:

```python
class ExampleView(PermafrostMixin, View):
    permission_required = ("example.view_report",)
    permission_required_post = ("example.change_report",)
```

For a `POST` request, Permafrost combines `permission_required` and `permission_required_post`.

### PermafrostSiteMixin

`PermafrostSiteMixin` checks permissions against the configured Permafrost context. Historically this meant `request.site`; with configurable context support it can also use a request-attached organization, team, or other context object.

Use this request-aware mixin for tenant-scoped view authorization. Django's
plain `user.has_perm()` call does not receive the request and therefore cannot
discover a request-attached organization or team.

### PermafrostLogMixin

`PermafrostLogMixin` logs failed permission checks to a configured logger:

```python
class ExampleView(PermafrostLogMixin, PermafrostMixin, View):
    permission_logger = "security.permissions"
```

The log entry includes request IP, user, method, path, user permissions, and required view permissions.

## Role Views

Permafrost includes class-based views for the common role workflow:

- `PermafrostRoleListView`
- `PermafrostRoleManageView`
- `PermafrostRoleDetailView`
- `PermafrostRoleCreateView`
- `PermafrostRoleUpdateView`
- `PermafrostRoleDeleteView`

These views filter roles to the current context object and exclude names listed in `PERMAFROST_EXCLUDED_ROLES`.

The role list and management sidebar support case-insensitive search across
role name, slug, and description, plus exact category filtering. Results use
`PERMAFROST_UI_PAGE_SIZE` and retain filter state while moving between pages
and role details. Filtering is applied only after the queryset has been
limited to the current request context.

## URLs

Include the package URLs in a project URLconf:

```python
from django.urls import include, path

urlpatterns = [
    path("roles/", include("permafrost.urls")),
]
```

The included namespace is `permafrost`.

## Role Membership

The built-in membership workflow is available at
`role/<slug>/users/` within the included URL namespace. It provides:

- a paginated, searchable list of current role members
- bulk addition by exact user identifier or primary key
- bulk removal of selected current members

`GET` requires `permafrost.view_permafrostrole`. Membership changes also
require `permafrost.add_user_to_role`. The role queryset is scoped to the
configured request context, so a role slug from another Team, Organization,
or Site is not available through this view.

Set the number of displayed members per page with:

```python
PERMAFROST_UI_PAGE_SIZE = 50
```

The value must be a positive integer. When
`PERMAFROST_API_USER_LOOKUP_FIELD` names a configured unique user field, the
add form accepts exact values for that field. Otherwise it accepts numeric
user primary keys. Multiple values may be separated by commas or line breaks;
the complete submission is rejected if any value is unknown.

Permafrost cannot infer which users belong to a host project's tenant. The
page lists only existing members and does not expose a global user directory.
Applications remain responsible for deciding which known user identifiers may
be assigned to a context-scoped role.

## Reverse Role Lookups

The read-only lookup workflow is available at `lookups/` within the included
URL namespace. It answers two context-scoped questions:

- Which Permafrost roles does this exact user hold?
- Which Permafrost roles grant this configured permission?

The user lookup uses `PERMAFROST_API_USER_LOOKUP_FIELD` when configured and
falls back to a numeric user primary key. It does not provide a global user
list or partial-name search. The permission lookup offers only permissions
declared by the developer in `PERMAFROST_CATEGORIES`.

Both result sets exclude deleted and configured excluded roles, are limited to
the current request context, use `PERMAFROST_UI_PAGE_SIZE`, and require
`permafrost.view_permafrostrole`. The same behavior is available without the
built-in templates through:

```python
services.list_user_roles(user, context_object=team)
services.list_permission_roles(permission, context_object=team)
services.list_exposed_permissions()
```

## Permission Editing

The role management views only expose permissions declared in `PERMAFROST_CATEGORIES`.

When optional permissions are submitted, updates are routed through the role permission helper methods. This keeps the UI aligned with the same permission allow-list enforced by the model.

## Bundled Template Scope

The built-in templates provide an optional, server-rendered management UI.
The default `permafrost/base.html` includes Bootstrap 4-compatible CSS and
JavaScript plus jQuery so the bundled modal workflow works without host
project setup. Applications with their own design system should override the
templates under the `permafrost/` template namespace.

Permafrost's Python form classes are framework-neutral: they use Django's
native widgets and do not add Bootstrap classes. This preserves Django's
generated required, disabled, validation, help-text, and ARIA attributes and
lets a host project style widgets through its own form renderer or template
overrides. Bootstrap-specific classes are confined to the bundled templates.
