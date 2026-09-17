# Project Roadmap

This is the running source of truth for planned django-permafrost work.

- Check off an item only after its implementation, tests, and relevant documentation are complete.
- Add newly discovered work here instead of leaving it only in a source-code comment or conversation.
- Keep release notes in `CHANGELOG.md`; this file tracks work before and after releases.
- Review priorities when opening a release branch or beginning a new feature.

Last reviewed: 2026-09-17 on `new/context-model-hardening`, based on `GitHub/develop` at `66412fe`.

## Current Release State

- Published PyPI release: `0.4.1`
- In-development release: `0.5.0`, introducing the service and optional DRF APIs
- Remote development baseline: `GitHub/develop` at `66412fe` after pull request #97
- Latest permission hardening commit: `b5328eb`, merged into `develop`
- Local test baseline: 97 passing tests on Python 3.14
- Package baseline: wheel and source distribution build successfully and pass `twine check`

## P0 - Integrate Current Work

- [x] Merge the API and permission hardening changes into `develop` through pull requests #96 and #97.
- [ ] Confirm the develop pull-request workflow passes at both supported compatibility endpoints.
- [ ] Promote the accumulated unreleased changes through the master compatibility matrix.
- [ ] Publish `0.5.0` after the API hardening changes and contributor metadata reach `master`.

Completion criteria: the hardening commit is on `master`, all required GitHub Actions pass, the release is present on PyPI, and `CHANGELOG.md` names the released version.

## P1 - Authorization And Tenant Safety

- [x] Audit the custom authentication backends for permission-cache leakage between contexts. Permafrost now bypasses Django's user-wide group/all-permission caches and has regression tests that switch contexts using the same user instance.
- [x] Define and test the supported authorization path for normal Django `user.has_perm()` calls versus request-aware `has_all_permissions()` checks.
- [x] Test every built-in HTML and HTTP API read/write path for cross-context object access, including guessed slugs and role membership changes. Service queries also default to the configured current context when no context is passed.
- [x] Reject existing but disallowed permission IDs in the service and HTTP APIs, without partially applying the submitted update. Lower-level model helpers retain defensive filtering.
- [x] Make role, group, permission, and membership mutations atomic so partial failures cannot leave orphaned or unconformed Django groups.

Completion criteria: tests demonstrate that one context cannot observe or reuse permissions, roles, or memberships from another context, including after Django permission caching.

## P1 - Context Model Completion

- [x] Make the legacy `site` field nullable for custom context models while preserving existing Site-based installations through migration `0021`.
- [x] Keep `django.contrib.sites` mandatory for `0.5.0` migration compatibility while allowing custom-context roles to store no Site value.
- [x] Delete roles and matching Groups when their configured context object is deleted.
- [x] Update Django admin list columns and filters to display the configured context instead of assuming Site.
- [x] Add realistic Team and TeamResource example models covering forms, views, services, and the HTTP API.
- [x] Add end-to-end Team A versus Team B authorization tests covering role permissions, API/HTML access, and application objects scoped by `team=request.team`.
- [x] Add system-check warning `permafrost.W002` when Django's global `ModelBackend` can bypass Permafrost context scoping for role-backed Group permissions.
- [x] Document trusted request-context resolution and independent business-object queryset scoping.
- [x] Preserve and explicitly test that authenticated superusers have all permissions in every configured context, regardless of role membership.
- [x] Add a complete Team-context setup guide covering settings, the Team model contract, middleware, authentication backends, role creation and assignment, request-aware permission checks, and context-scoped querysets.
- [x] Document the authorization flow from `request.team` through `PermafrostRole`, Django Group membership, permission evaluation, and object lookup, including Team A/Team B and superuser examples.
- [x] Document common unsafe configurations and failure modes, especially the default `ModelBackend`, unscoped `user.has_perm()` calls, untrusted context selection, and business-object queries that omit the current Team.
- [x] Align the README and detailed installation, models, views, and API documentation with the tested Team example.

Completion criteria: a developer can configure and understand a non-Site context using repository documentation alone; the project works without placeholder Site relationships; Team permissions and business objects cannot cross contexts; superusers retain unrestricted access; and the upgrade path for existing projects is documented and tested.

## P1 - Role Integrity

- [ ] Prevent slug collisions within a context. Different names such as `Support Team` and `Support-Team` currently produce the same slug even though uniqueness is enforced on `name`.
- [ ] Define stable slug behavior when a role is renamed and document whether URLs should change.
- [ ] Review Django Group naming for length limits and collisions across context models, context IDs, categories, and role slugs.
- [ ] Ensure deleting a role cannot delete a Django Group that is referenced elsewhere.
- [ ] Validate malformed category entries without raising unexpected exceptions, including non-dictionary permission items and missing labels.

Completion criteria: database constraints and model validation protect all role identifiers and group relationships, with migration and regression coverage.

## P2 - API Productization

- [ ] Add pagination, ordering, and documented filtering/search behavior for role and membership lists.
- [ ] Decide whether membership lookup should support username, email, or project-defined identifiers in addition to primary keys.
- [ ] Add an explicit API versioning policy before downstream projects depend on the current URL and response shapes.
- [ ] Add OpenAPI schema support and response examples without making DRF mandatory for service-layer users.
- [ ] Add a CI job that installs the base package without DRF and verifies imports, checks, migrations, and service usage.
- [ ] Define supported DRF versions and add bounds or compatibility jobs if the HTTP API is treated as a stable public feature.

Completion criteria: the HTTP API has a documented stability contract and is independently tested both with and without the optional DRF dependency.

## P2 - Built-In UI And Admin

- [ ] Finish role-user list and bulk membership workflows, with pagination for large tenants.
- [ ] Add user-to-role and permission-to-role lookup workflows if they remain in package scope.
- [ ] Replace the remaining template TODOs for role search/filtering and long-list behavior with implemented features or remove them from scope.
- [ ] Review the bundled templates against current Django accessibility and form-rendering practices.
- [ ] Decide whether Bootstrap-specific form mutation remains part of the reusable package or moves to example/project code.

Completion criteria: the supported UI scope is explicit, tested, accessible, and independent of undocumented frontend assumptions.

## P2 - Quality And Maintainability

- [ ] Split the large `src/permafrost/tests.py` module into focused model, context, permission, view, form, service, and API test modules.
- [ ] Convert stale source TODO comments into roadmap items, actionable issues, or completed code and remove obsolete commented-out code.
- [ ] Add CI enforcement for the quality tools already declared in project extras, or remove tools that the project does not intend to enforce.
- [ ] Add coverage reporting and establish a practical minimum after the test suite is organized.
- [ ] Review import-time settings constants so tests and reusable integrations behave predictably under `override_settings`.
- [ ] Correct or deprecate legacy public naming such as the `permcatagories` command without surprising existing users.

Completion criteria: local and CI commands are documented, deterministic, and enforce only tools the project actively maintains.

## P3 - Documentation And Release Operations

- [ ] Add a complete custom-context tutorial with middleware and an Organization/Team model.
- [ ] Add upgrade documentation from `0.4.x` to `0.5.x`, including schema and settings decisions.
- [ ] Document authentication-backend setup and the boundary between global Django permissions and context-scoped Permafrost permissions.
- [ ] Add API error-response and authorization examples.
- [ ] Decide on a documentation builder and publishing target, then validate docs in CI.
- [ ] Add a release checklist covering version consistency, changelog finalization, full matrix results, PyPI trusted publishing, Sigstore output, and GitHub Release verification.
- [ ] Define a policy for supported Django/Python prereleases; Python 3.15 and unreleased Django combinations should be allowed to fail only when explicitly marked experimental.

Completion criteria: a new maintainer can configure, test, release, and troubleshoot the package using repository documentation alone.

## Completed Foundation

- [x] Restored the Git repository history and normal branch-based workflow.
- [x] Established Python 3.11-3.15 and Django 5.2-6.1 package metadata and CI targets.
- [x] Dropped unsupported Django 5.1 and older versions.
- [x] Replaced legacy dependency handling with `pyproject.toml` and optional extras.
- [x] Added configurable context model and request attribute settings while preserving Site defaults.
- [x] Added system checks for core Permafrost configuration.
- [x] Routed role permission changes through guarded model helpers.
- [x] Split lightweight develop PR tests from the full master compatibility matrix.
- [x] Separated manual version bumping from master-only publishing.
- [x] Updated artifact, publishing, and signing actions and verified the release workflow.
- [x] Added package-data configuration and verified wheel/source distributions.
- [x] Added repository guidance, a changelog, and expanded architecture/setup documentation.
- [x] Added a DRF-independent service API and optional DRF HTTP API.
- [x] Added API tests for context scoping, invalid identifiers, role membership, soft deletion, and optional DRF isolation.
- [x] Corrected package attribution for Grant Viklund and Devon Jackson for the next release metadata.
