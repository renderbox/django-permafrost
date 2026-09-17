from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

try:
    from rest_framework.pagination import PageNumberPagination
except ImportError as exc:
    raise ImproperlyConfigured(
        "Django REST Framework is required to use permafrost.api.pagination. "
        "Install djangorestframework to enable the Permafrost HTTP API."
    ) from exc


class PermafrostPageNumberPagination(PageNumberPagination):
    page_size_query_param = "page_size"

    def get_page_size(self, request):
        self.page_size = getattr(settings, "PERMAFROST_API_PAGE_SIZE", 50)
        self.max_page_size = getattr(settings, "PERMAFROST_API_MAX_PAGE_SIZE", 200)
        return super().get_page_size(request)
