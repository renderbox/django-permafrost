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

## Permission Editing

The role management views only expose permissions declared in `PERMAFROST_CATEGORIES`.

When optional permissions are submitted, updates are routed through the role permission helper methods. This keeps the UI aligned with the same permission allow-list enforced by the model.
