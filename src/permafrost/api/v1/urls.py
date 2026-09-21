from django.core.exceptions import ImproperlyConfigured
from django.urls import include, path

try:
    from rest_framework.routers import SimpleRouter
except ImportError as exc:
    raise ImproperlyConfigured(
        "Django REST Framework and drf-spectacular are required to use "
        "permafrost.api.v1.urls. Install django-permafrost[api] to enable "
        "the Permafrost HTTP API."
    ) from exc

from permafrost.api.views import PermafrostRoleViewSet
from permafrost.api.schema import PermafrostSchemaView

app_name = "v1"

router = SimpleRouter()
router.register("roles", PermafrostRoleViewSet, basename="role")

urlpatterns = [
    path(
        "schema/",
        PermafrostSchemaView.as_view(),
        name="schema",
    ),
    path("", include(router.urls)),
]
