# About

Django Permafrost is a small role-management layer over Django's native auth system.

It does not replace Django permissions. Instead, it curates which permissions can be exposed to client or tenant administrators and stores the resulting assignments on normal Django `Group` records.

## Architecture

The main pieces are:

- `PermafrostRole`: the tenant-scoped role model.
- Django `Group`: the actual permission and user membership container.
- Django `Permission`: the underlying permissions assigned to the group.
- `PERMAFROST_CATEGORIES`: developer-owned configuration that defines required and optional permissions.
- Context helpers: utilities that resolve the current `Site`, `Organization`, `Team`, or other configured context model.
- Views and forms: UI helpers for creating, updating, listing, and managing roles.

## Permission Model

Developers decide which permissions are available by defining `PERMAFROST_CATEGORIES`.

Each category can include:

- `required`: permissions always applied to roles in that category
- `optional`: permissions tenant administrators may choose to add
- `label`: display label
- `access_level`: project-defined sorting or grouping value

The role methods `permissions_add`, `permissions_remove`, `permissions_set`, and `permissions_clear` enforce those category rules before mutating the attached group.

## Tenant Scoping

Roles are scoped by context:

- Default: `sites.Site`
- Configurable: any installed Django model, such as `accounts.Organization`

The role stores context using Django's content type framework. This allows reusable package code while still letting each project choose its own tenant anchor.

The configured context model should be stable for the life of the project.

## Current State

The project is usable as shared functionality for modern Django projects, especially when a project wants Django-native permissions and groups rather than a separate authorization engine.

The strongest parts are:

- use of Django auth primitives
- explicit permission allow-lists through categories
- automatic group creation and conformity
- tenant-scoped role lookup
- local test coverage for the core role and view workflows

The areas that still deserve hardening are:

- fuller documentation examples
- clearer public API boundaries
- admin polish for custom context models
- compatibility verification across the full GitHub Actions matrix
- release process verification on GitHub
