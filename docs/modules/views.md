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

## Permission Editing

The role management views only expose permissions declared in `PERMAFROST_CATEGORIES`.

When optional permissions are submitted, updates are routed through the role permission helper methods. This keeps the UI aligned with the same permission allow-list enforced by the model.
