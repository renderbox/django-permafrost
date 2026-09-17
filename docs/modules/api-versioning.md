# API Versioning

## HTTP API

The optional HTTP API uses a major version in every URL. Version 1 is
introduced with django-permafrost 0.5.0 and is mounted below `/v1/`:

```text
/api/permafrost/v1/roles/
```

The prefix before `/v1/` is chosen by the host project when it includes
`permafrost.api.urls`. Permafrost does not expose unversioned HTTP routes and
does not select versions through headers or query parameters.

Projects can reverse version 1 routes through the nested Django namespace:

```python
reverse("permafrost_api:v1:role-list")
```

### Compatibility Policy

The following changes may be made within an existing HTTP API major version:

- adding endpoints or optional request fields
- adding response fields
- adding optional filters and ordering fields
- correcting behavior that violates the documented contract
- tightening authorization, tenant isolation, or input validation to address a security issue

The following changes require a new HTTP API major version:

- removing or renaming an endpoint or documented field
- changing a documented field's type or meaning
- making an optional request field required
- changing the documented success response shape
- replacing the authentication or pagination contract

Bug and security fixes may cause previously invalid or unauthorized requests to
be rejected without creating a new API major version.

### Deprecation Policy

When a replacement major version is introduced, the changelog and API
documentation will identify the deprecated version and its migration path.
Permafrost will normally retain the older major version for at least one
subsequent feature release. Removal will not occur in a patch release unless a
security issue makes continued support unsafe.

## Python Service API

The functions in `permafrost.api.services` are a Python package API rather than
an HTTP API, so they do not use URL-style versions. Their compatibility follows
the django-permafrost package version and release notes. During the pre-1.0
series, breaking Python API changes may occur in a feature release, but should
be documented with an upgrade path; patch releases should remain compatible
apart from necessary bug or security corrections.
