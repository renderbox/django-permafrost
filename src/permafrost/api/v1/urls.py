from django.core.exceptions import ImproperlyConfigured
from django.urls import include, path

try:
    from rest_framework.routers import DefaultRouter
except ImportError as exc:
    raise ImproperlyConfigured(
        "Django REST Framework is required to use permafrost.api.v1.urls. "
        "Install djangorestframework to enable the Permafrost HTTP API."
    ) from exc

from permafrost.api.views import PermafrostRoleViewSet

app_name = "v1"

router = DefaultRouter()
router.register("roles", PermafrostRoleViewSet, basename="role")

urlpatterns = [
    path("", include(router.urls)),
]
