# django-permafrost Agent Notes

These notes are for coding agents working in this repository.

## Project Direction

`django-permafrost` is a reusable Django app that builds tenant-scoped role management on top of Django's native `auth.Group` and `auth.Permission` models.

The project should stay small, Django-native, and suitable for reuse across multiple multi-tenant Django projects.

## Compatibility Targets

- Support Python 3.11 and newer.
- Support Django 5.2 through the latest configured upper bound in `pyproject.toml`.
- Do not reintroduce support for Django 5.1 or older unless the project metadata and test matrix are deliberately changed.
- Keep `pyproject.toml`, README, docs, and GitHub Actions aligned when compatibility targets change.

## Changelog

Always maintain `CHANGELOG.md`.

Update it for:

- user-facing behavior changes
- migrations or schema changes
- settings changes
- compatibility changes
- dependency or packaging changes
- CI/release workflow changes
- security or hardening fixes
- backwards compatibility notes

Add entries before a release is published. Prefer concise bullets under the current or next release version.

## Roadmap

Always maintain `TODO.md` as the running source of truth for planned work.

- Add newly discovered bugs, hardening work, and feature decisions to the appropriate priority section.
- Check off an item only after implementation, tests, and relevant documentation are complete.
- Update the review date and release-state snapshot when performing a project-status review.
- Keep completed foundation work for historical context, but move routine completed tasks to `CHANGELOG.md` instead of growing the roadmap indefinitely.
- Do not use `TODO.md` as release notes; user-facing completed changes belong in `CHANGELOG.md`.

## Documentation

Keep documentation changes close to behavior changes.

When changing setup, settings, permissions, tenant context behavior, packaging, or supported versions, update the relevant files:

- `README.md` for the quick-start and public overview
- `docs/modules/installation.md` for setup and upgrade guidance
- `docs/modules/models.md` for model/context/permission behavior
- `docs/modules/views.md` for view and mixin behavior
- `docs/modules/team-context.md` for custom tenant setup and isolation behavior
- `docs/modules/about.md` for architecture and maintenance notes
- `CHANGELOG.md` for release-facing change history

## Context Model

Permafrost roles default to Django's `sites.Site` model as their context.

Projects may configure another context model with:

```python
PERMAFROST_CONTEXT_MODEL = "app_label.ModelName"
PERMAFROST_CONTEXT_REQUEST_ATTR = "organization"
```

Treat `PERMAFROST_CONTEXT_MODEL` like `AUTH_USER_MODEL`: it should be set before production data exists and should not be changed casually after roles have been created.

Preserve the default Site behavior unless a change is explicitly intended to be backwards incompatible.

## Permission Safety

Do not bypass the `PermafrostRole` permission helper methods in role management workflows.

Prefer:

```python
role.permissions_add(...)
role.permissions_remove(...)
role.permissions_set(...)
role.permissions_clear()
```

Avoid direct mutation through `role.group.permissions.*` in application-facing code unless there is a specific reason and tests cover the bypass.

## Tests

For local verification, run:

```shell
cd develop
../venv/bin/python manage.py test permafrost
```

For package verification, run from the repository root:

```shell
venv/bin/python -m build
venv/bin/python -m twine check dist/*
```

If build artifacts should not be left in the repo, build to a temporary output directory:

```shell
venv/bin/python -m build --outdir /tmp/django-permafrost-dist-check
venv/bin/python -m twine check /tmp/django-permafrost-dist-check/*
```

## Packaging

Runtime dependencies belong in `pyproject.toml`.

Do not reintroduce a root `requirements.txt` for package runtime dependencies. Use optional dependency groups in `pyproject.toml` for development, testing, and docs.

When package data changes, check both:

- `MANIFEST.in`
- `[tool.setuptools.package-data]` in `pyproject.toml`

Templates, fixtures, migrations, docs, README, license, and changelog should be present where appropriate in build artifacts.

## GitHub Actions

The intended workflow split is:

- develop PRs: lighter compatibility checks
- master PRs: broader compatibility matrix
- version bump: manual workflow, separate from publishing
- publish: manual workflow, master-only source, PyPI publish, Sigstore signing, GitHub release

Keep publish control conservative. Do not combine version bumping and publishing without explicit project direction.

Keep GitHub Actions pinned to current, supported action versions.

## Editing Guidance

- Keep changes focused and consistent with existing Django patterns.
- Avoid unrelated refactors during compatibility, packaging, or release work.
- Do not remove legacy compatibility fields, such as the `site` field, unless a migration and upgrade plan are included.
- Add or update tests when changing role behavior, permission filtering, context resolution, forms, views, or migrations.
