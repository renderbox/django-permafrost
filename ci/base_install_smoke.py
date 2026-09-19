"""Exercise the installed base wheel without HTTP API dependencies."""

from importlib.util import find_spec
from pathlib import Path

from django.conf import settings

assert find_spec("rest_framework") is None, "DRF must not be installed"
assert find_spec("drf_spectacular") is None, "drf-spectacular must not be installed"

settings.configure(
    SECRET_KEY="permafrost-base-install-smoke",
    INSTALLED_APPS=[
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sites",
        "permafrost",
    ],
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    SITE_ID=1,
    AUTHENTICATION_BACKENDS=[
        "permafrost.backends.PermafrostModelBackend",
    ],
    PERMAFROST_CATEGORIES={
        "administration": {
            "label": "Administration",
            "required": [],
            "optional": [],
        },
        "staff": {
            "label": "Staff",
            "required": [],
            "optional": [],
        },
        "user": {
            "label": "User",
            "required": [],
            "optional": [
                {
                    "label": "Can view user",
                    "permission": ("view_user", "auth", "user"),
                }
            ],
        },
    },
    PERMAFROST_DEFAULT_ROLES=[],
    USE_TZ=True,
)

import django

django.setup()

import permafrost
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command

from permafrost.api import services
import permafrost.urls  # noqa: F401

package_path = Path(permafrost.__file__).resolve()
assert (
    "site-packages" in package_path.parts
), f"Expected the installed wheel, imported {package_path}"

call_command("migrate", interactive=False, verbosity=0)
call_command("check", verbosity=0)
try:
    call_command("makemigrations", check=True, dry_run=True, verbosity=0)
except SystemExit as exc:
    assert exc.code == 0, "Model changes are missing migrations"

site, _ = Site.objects.update_or_create(
    pk=1,
    defaults={"domain": "example.test", "name": "Example"},
)
user = get_user_model().objects.create_user(
    username="base-install-user",
    password="not-used",
)
permission = Permission.objects.get_by_natural_key("view_user", "auth", "user")

role = services.create_role(
    name="Base Install Role",
    category="user",
    permissions=[permission],
    context_object=site,
)
assert services.get_role(role.slug, context_object=site) == role
assert list(services.list_role_permissions(role)) == [permission]

services.add_role_users(role, [user])
assert list(services.list_role_users(role)) == [user]

services.update_role(role, description="Updated through the service API")
role.refresh_from_db()
assert role.description == "Updated through the service API"

services.remove_role_users(role, [user])
assert not services.list_role_users(role).exists()

services.delete_role(role)
role.refresh_from_db()
assert role.deleted is True

for module_name in (
    "permafrost.api.pagination",
    "permafrost.api.permissions",
    "permafrost.api.schema",
    "permafrost.api.serializers",
    "permafrost.api.urls",
    "permafrost.api.views",
    "permafrost.api.v1.urls",
):
    try:
        __import__(module_name)
    except ImproperlyConfigured as exc:
        assert "required" in str(exc).lower()
    else:
        raise AssertionError(f"{module_name} imported without HTTP API dependencies")

print("Base wheel works without DRF or drf-spectacular.")
