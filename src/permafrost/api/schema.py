from django.core.exceptions import ImproperlyConfigured

try:
    from drf_spectacular.generators import SchemaGenerator
    from drf_spectacular.openapi import AutoSchema
    from drf_spectacular.renderers import (
        OpenApiJsonRenderer,
        OpenApiJsonRenderer2,
        OpenApiYamlRenderer,
        OpenApiYamlRenderer2,
    )
    from drf_spectacular.settings import patched_settings
    from rest_framework.permissions import AllowAny
    from rest_framework.response import Response
    from rest_framework.views import APIView
except ImportError as exc:
    raise ImproperlyConfigured(
        "Django REST Framework and drf-spectacular are required to use "
        "permafrost.api.schema. Install django-permafrost[api] to enable "
        "the Permafrost HTTP API schema."
    ) from exc


class ExcludedAutoSchema(AutoSchema):
    def is_excluded(self):
        return True


class PermafrostSchemaView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    renderer_classes = [
        OpenApiYamlRenderer,
        OpenApiYamlRenderer2,
        OpenApiJsonRenderer,
        OpenApiJsonRenderer2,
    ]
    schema = ExcludedAutoSchema()

    def get(self, request):
        schema_base_path = request.path.removesuffix("schema/")
        with patched_settings(
            {
                "TITLE": "Django Permafrost HTTP API",
                "DESCRIPTION": "Tenant-aware role and permission management.",
                "VERSION": "1.0.0",
                "SERVERS": [
                    {
                        "url": schema_base_path,
                        "description": "Permafrost v1 API",
                    }
                ],
            }
        ):
            schema = SchemaGenerator(
                urlconf="permafrost.api.v1.urls",
            ).get_schema(request=request, public=True)
        return Response(
            schema,
            headers={"Content-Disposition": 'inline; filename="permafrost-v1"'},
        )
