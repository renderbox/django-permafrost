# Changelog

## 0.5.0 - 2026-09-21

### Changed

- Clarified package author/contributor metadata and project README attribution.
- Made the legacy `PermafrostRole.site` relationship nullable so custom context models do not require placeholder Site records.
- Updated Django admin role lists to display the configured context object instead of assuming Site.
- Enforced exclusive one-to-one ownership between each Permafrost role and its Django Group.
- Kept role slugs tied to role names while enforcing slug uniqueness within each context.
- Bounded generated Group names to Django's field limit with deterministic hash suffixes for long names.
- Defined the optional HTTP API dependency contract as Django REST Framework 3.16 through 3.18 and drf-spectacular 0.30.x.

### Added

- Added a DRF-independent Python service API under `permafrost.api.services`.
- Added optional Django REST Framework serializers, views, permissions, and URLs under `permafrost.api`.
- Added a `django-permafrost[api]` optional dependency extra for HTTP API users.
- Added API hardening tests for optional DRF behavior, context scoping, invalid payloads, soft deletion, and role membership changes.
- Added a real Team context example and end-to-end Team A/Team B isolation tests for services, HTML views, the HTTP API, business objects, context deletion, and superusers.
- Added a system-check warning for Django's global `ModelBackend` and a complete Team-context setup guide.
- Added page-number pagination, search, exact filters, and controlled ordering for HTTP API role and membership collections.
- Added configurable `PERMAFROST_API_PAGE_SIZE` and `PERMAFROST_API_MAX_PAGE_SIZE` settings with system checks.
- Added opt-in membership lookup by a configured unique custom-user field, with bulk add/remove support and system checks.
- Added an explicit `/v1/` HTTP API boundary and documented compatibility and deprecation policies.
- Added a public OpenAPI 3.0 schema with typed operations, stable operation IDs, and request/response examples.
- Added CI coverage that installs the base wheel without HTTP API extras and exercises checks, migrations, and service operations.
- Added HTTP API compatibility jobs covering representative Django 5.2, 6.0, and 6.1 combinations across the supported DRF range.

### Fixed

- API payloads now return validation errors for unknown permission IDs or user IDs instead of silently ignoring them.
- API role updates now keep `category` immutable after creation.
- Prevented Django's user-wide permission caches from carrying Permafrost group permissions between tenant contexts.
- Scoped service API role queries to the configured current context when callers do not pass a request or context explicitly.
- Service and HTTP API permission updates now reject permissions outside the role category instead of silently dropping them.
- Made role/group lifecycle and service-layer mutations transactional to prevent partially saved roles, groups, permissions, or memberships.
- Reject context objects that do not match `PERMAFROST_CONTEXT_MODEL`.
- Delete context-scoped roles and their Groups when the configured context object is deleted.
- Reject role names that normalize to an existing context slug or an empty slug.
- Prevent new roles from adopting unrelated existing Django Groups with matching generated names.
- Report malformed category labels, permission entries, and permission natural keys through Django system checks instead of raising unexpected exceptions.

## 0.4.0

### Changed

- Modernized package metadata around `pyproject.toml`.
- Updated supported runtime targets to Python 3.11+ and Django 5.2 through 6.1.
- Removed the legacy `requirements.txt` in favor of project dependencies and optional dependency groups.
- Split GitHub Actions into lighter develop PR tests, broader master PR tests, manual version bumping, and manual publishing.
- Updated GitHub Actions to current action majors for checkout, Python setup, artifact upload/download, PyPI publishing, and Sigstore signing.

### Added

- Added configurable role context anchoring with `PERMAFROST_CONTEXT_MODEL`.
- Added `PERMAFROST_CONTEXT_REQUEST_ATTR` for projects that attach the current tenant or organization to the request.
- Added content type backed context fields to `PermafrostRole` while preserving the default Django `Site` behavior.
- Added system checks for common Permafrost settings problems.
- Added packaging configuration for bundled templates and fixtures.

### Fixed

- Routed role permission updates through `PermafrostRole` permission helpers so submitted permissions are checked against configured optional and required permissions.
- Hardened system checks so they do not fail during early migration/database setup.

### Upgrade Notes

- Django 5.1 and older are no longer supported. Start new projects on Django 5.2 or newer.
- Existing Site-based projects can keep using the default `PERMAFROST_CONTEXT_MODEL = "sites.Site"`.
- Projects that want roles scoped to another model should set `PERMAFROST_CONTEXT_MODEL` before creating production role data.
- Each project should treat the configured context model as a long-lived schema decision, similar to `AUTH_USER_MODEL`.
