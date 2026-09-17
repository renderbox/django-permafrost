# Project Roadmap

This is the running source of truth for planned django-permafrost work.

- Check off an item only after its implementation, tests, and relevant documentation are complete.
- Add newly discovered work here instead of leaving it only in a source-code comment or conversation.
- Keep release notes in `CHANGELOG.md`; this file tracks work before and after releases.
- Review priorities when opening a release branch or beginning a new feature.

Last reviewed: 2026-09-16 on `new/drf-api` at `215c4c6`.

## Current Release State

- Published PyPI release: `0.4.1`
- In-development release: `0.5.0`, introducing the service and optional DRF APIs
- Development baseline: `develop` at `faa2041`
- Local API hardening commit: `new/drf-api` at `215c4c6`
- Local test baseline: 76 passing tests on Python 3.14
- Package baseline: wheel and source distribution build successfully and pass `twine check`

## P0 - Integrate Current Work

- [ ] Push `215c4c6` and merge the API hardening changes into `develop` through a pull request.
- [ ] Confirm the develop pull-request workflow passes at both supported compatibility endpoints.
- [ ] Promote the accumulated unreleased changes through the master compatibility matrix.
- [ ] Publish `0.5.0` after the API hardening changes and contributor metadata reach `master`.

Completion criteria: the hardening commit is on `master`, all required GitHub Actions pass, the release is present on PyPI, and `CHANGELOG.md` names the released version.

## P1 - Authorization And Tenant Safety

- [ ] Audit the custom authentication backends for permission-cache leakage between contexts. Django's normal `_group_perm_cache` is user-wide, while Permafrost permissions are context-specific; add regression tests that switch contexts using the same user instance.
- [ ] Define and test the supported authorization path for normal Django `user.has_perm()` calls versus request-aware `has_all_permissions()` checks.
- [ ] Test every built-in HTML and HTTP API read/write path for cross-context object access, including guessed slugs and role membership changes.
- [ ] Decide whether existing but disallowed permission IDs should be rejected by the service and HTTP APIs instead of silently ignored. Document the contract and test the chosen behavior.
- [ ] Make role, group, permission, and membership mutations atomic so partial failures cannot leave orphaned or unconformed Django groups.

Completion criteria: tests demonstrate that one context cannot observe or reuse permissions, roles, or memberships from another context, including after Django permission caching.

## P1 - Context Model Completion

- [ ] Design the migration path that makes the legacy `site` field optional for projects using a custom context model while preserving existing Site-based installations.
- [ ] Decide whether `django.contrib.sites` remains a mandatory dependency or becomes conditional when a custom context model is configured.
- [ ] Define deletion behavior for a context object. Generic foreign keys do not provide database-enforced cascading, so orphaned roles need an explicit policy.
- [ ] Update Django admin list columns and filters to present the configured context rather than always displaying `site`.
- [ ] Add a realistic example project and tests using an `Organization` or `Team` model, including migrations, forms, views, services, and the HTTP API.

Completion criteria: a new project can use a non-Site context without creating placeholder Site relationships, and the upgrade path for existing projects is documented and tested.

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
