# Team Context Setup

This guide configures Permafrost so every role and permission assignment is
anchored to a project-owned `Team` model. The same pattern works for an
`Organization`, `Account`, or another tenant model.

## Model

The context model must be installed before Permafrost roles are created. A
`get_current()` manager method is only required when code needs to resolve a
context without a request or an explicit `context_object`.

```python
from django.conf import settings
from django.db import models


class TeamManager(models.Manager):
    def get_current(self):
        return self.get(pk=settings.CURRENT_TEAM_ID)


class Team(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    objects = TeamManager()
```

Most multi-tenant applications should pass the Team explicitly or attach it to
the request. A process-wide `CURRENT_TEAM_ID` is mainly useful for management
commands, tests, or installations that truly have one default Team.

## Settings

```python
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "teams",
    "permafrost",
]

PERMAFROST_CONTEXT_MODEL = "teams.Team"
PERMAFROST_CONTEXT_REQUEST_ATTR = "team"

AUTHENTICATION_BACKENDS = [
    "permafrost.backends.PermafrostModelBackend",
]
```

`django.contrib.sites` remains required in `0.5.0` for backwards-compatible
migrations and the legacy nullable `site` field. Team-backed roles do not need
a Site value and are stored with `site_id=None`.

Do not add Django's global `ModelBackend` alongside the Permafrost backend
unless global Group permissions are intentional. Django combines successful
answers from every backend, and `ModelBackend` does not know which Team is
active.

## Trusted Request Context

Resolve the Team from a trusted part of the request, such as a validated URL
slug or subdomain. Do not accept an arbitrary Team ID from a client header
unless a trusted gateway validates and rewrites that header.

For routes containing `<slug:team_slug>`, middleware can attach the Team before
the view performs its permission check:

```python
from django.shortcuts import get_object_or_404

from teams.models import Team


class TeamContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        team_slug = view_kwargs.get("team_slug")
        if team_slug is not None:
            request.team = get_object_or_404(Team, slug=team_slug)
```

Place this middleware after Django's authentication middleware when Team
resolution also depends on `request.user`.

## Creating And Assigning Roles

Pass the Team explicitly when application code creates a role:

```python
from permafrost.api import services

role = services.create_role(
    name="Team Administrator",
    category="administration",
    context_object=team,
)
services.add_role_users(role, [user])
```

The role owns a normal Django Group, but Permafrost records that the role and
its Group permissions belong to this specific Team.

## Checking Permissions

For request handling, use a request-aware Permafrost API:

```python
from permafrost.permissions import has_all_permissions

allowed = has_all_permissions(request, ["billing.change_invoice"])
```

The check joins the authenticated user to Permafrost role Groups and filters
those roles by the content type and primary key of `request.team`. A permission
from Team A therefore does not satisfy the same check while Team B is active.

The bundled `PermafrostSiteMixin` and optional DRF API permission class perform
this request-aware check automatically. Despite its historical name,
`PermafrostSiteMixin` uses the configured context model and works with Teams.

Plain `user.has_perm()` does not receive the request. Use it only when the
configured context model's `get_current()` method reliably identifies the
correct Team. Request-aware checks are the recommended path for applications
where users can switch Teams.

## Scoping Application Objects

A permission check establishes what the user may do in the active Team. The
application must separately ensure that the object being read or changed also
belongs to that Team:

```python
from django.shortcuts import get_object_or_404

invoice = get_object_or_404(
    Invoice,
    pk=invoice_id,
    team=request.team,
)
```

For class-based views, combine permission and queryset scoping:

```python
from django.views.generic import UpdateView
from permafrost.views import PermafrostSiteMixin


class InvoiceUpdateView(PermafrostSiteMixin, UpdateView):
    model = Invoice
    permission_required = ("billing.change_invoice",)

    def get_queryset(self):
        return super().get_queryset().filter(team=self.request.team)
```

Without the queryset filter, a user authorized in Team A could potentially
submit the primary key of an object owned by Team B.

## Superusers

Authenticated Django superusers intentionally have all permissions in every
Permafrost context. They do not need role membership. Querysets should still be
scoped when the interface is intended to display only the currently selected
Team; authorization bypass does not require mixing tenant data in one response.

## Context Deletion

Deleting a configured context object deletes its Permafrost roles. Deleting a
role also deletes its matching Django Group. Other Teams and their roles are
not affected.

## Authorization Flow

For a normal request, authorization follows this sequence:

1. Middleware resolves and attaches `request.team`.
2. A Permafrost view or API permission identifies the required permission.
3. Permafrost finds the user's role-backed Groups for that exact Team.
4. The permission check succeeds only if one of those Groups grants every
   required permission, or the user is a superuser.
5. The application queryset limits the requested business object to the same
   Team.

Both the permission check and object lookup are required for complete tenant
isolation.
