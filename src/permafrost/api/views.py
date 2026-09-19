from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404

from permafrost.api import services

try:
    from drf_spectacular.openapi import AutoSchema
    from drf_spectacular.types import OpenApiTypes
    from drf_spectacular.utils import (
        OpenApiExample,
        OpenApiParameter,
        extend_schema,
        extend_schema_view,
    )
    from rest_framework import filters, serializers, status, viewsets
    from rest_framework.decorators import action
    from rest_framework.response import Response
except ImportError as exc:
    raise ImproperlyConfigured(
        "Django REST Framework and drf-spectacular are required to use "
        "permafrost.api.views. Install django-permafrost[api] to enable the "
        "Permafrost HTTP API."
    ) from exc

from permafrost.api.permissions import PermafrostAPIPermission
from permafrost.api.pagination import PermafrostPageNumberPagination
from permafrost.api.serializers import (
    CategorySerializer,
    PermafrostRoleSerializer,
    PermafrostRoleWriteSerializer,
    PermissionSerializer,
    RolePermissionsWriteSerializer,
    RoleUsersWriteSerializer,
    UserSerializer,
)

ROLE_EXAMPLE = OpenApiExample(
    "Role response",
    value={
        "id": 7,
        "name": "Account Manager",
        "slug": "account-manager",
        "description": "Can help manage account-level tasks.",
        "category": "staff",
        "locked": False,
        "deleted": False,
        "permissions": [
            {
                "id": 12,
                "name": "Can view user",
                "codename": "view_user",
                "app_label": "auth",
                "model": "user",
                "natural_key": ["view_user", "auth", "user"],
            }
        ],
    },
    response_only=True,
    status_codes=["200", "201"],
)

VALIDATION_ERROR_EXAMPLE = OpenApiExample(
    "Validation error",
    value={"permission_ids": ["Unknown permission IDs: [999999]"]},
    response_only=True,
    status_codes=["400"],
)

MEMBERSHIP_IDS_EXAMPLE = OpenApiExample(
    "Users by primary key",
    value={"user_ids": [42, 43]},
    request_only=True,
)

MEMBERSHIP_IDENTIFIERS_EXAMPLE = OpenApiExample(
    "Users by configured identifier",
    value={"user_identifiers": ["grant", "devon"]},
    request_only=True,
)


@extend_schema_view(
    list=extend_schema(
        summary="List roles in the current context",
        responses={200: PermafrostRoleSerializer(many=True)},
    ),
    create=extend_schema(
        summary="Create a role in the current context",
        responses={
            201: PermafrostRoleSerializer,
            400: OpenApiTypes.OBJECT,
        },
        examples=[ROLE_EXAMPLE, VALIDATION_ERROR_EXAMPLE],
    ),
    retrieve=extend_schema(
        summary="Retrieve a role from the current context",
        responses={200: PermafrostRoleSerializer, 404: OpenApiTypes.OBJECT},
        examples=[ROLE_EXAMPLE],
    ),
    update=extend_schema(
        summary="Replace editable role fields",
        responses={
            200: PermafrostRoleSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        examples=[ROLE_EXAMPLE, VALIDATION_ERROR_EXAMPLE],
    ),
    partial_update=extend_schema(
        summary="Update editable role fields",
        responses={
            200: PermafrostRoleSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        examples=[ROLE_EXAMPLE, VALIDATION_ERROR_EXAMPLE],
    ),
    destroy=extend_schema(
        summary="Soft-delete a role",
        responses={204: None, 404: OpenApiTypes.OBJECT},
    ),
)
class PermafrostRoleViewSet(viewsets.ModelViewSet):
    schema = AutoSchema()
    lookup_field = "slug"
    permission_classes = [PermafrostAPIPermission]
    pagination_class = PermafrostPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "slug", "description"]
    ordering_fields = ["name", "slug", "category", "locked", "id"]
    ordering = ["name", "id"]

    def filter_queryset(self, queryset):
        if self.action == "list":
            return super().filter_queryset(queryset)
        return queryset

    def get_queryset(self):
        queryset = services.list_roles(request=self.request)
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)

        locked = self.request.query_params.get("locked")
        if locked is not None:
            boolean_values = {
                "true": True,
                "1": True,
                "false": False,
                "0": False,
            }
            try:
                queryset = queryset.filter(locked=boolean_values[locked.lower()])
            except KeyError as exc:
                raise serializers.ValidationError(
                    {"locked": "Use true, false, 1, or 0."}
                ) from exc

        return queryset

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PermafrostRoleWriteSerializer
        return PermafrostRoleSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.save()
        return Response(
            PermafrostRoleSerializer(role).data, status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        role = self.get_object()
        serializer = self.get_serializer(role, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        role = serializer.save()
        return Response(PermafrostRoleSerializer(role).data)

    def destroy(self, request, *args, **kwargs):
        role = self.get_object()
        services.delete_role(role, soft=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="List configured role categories",
        responses={200: CategorySerializer(many=True)},
        examples=[
            OpenApiExample(
                "Category response",
                value=[
                    {
                        "key": "staff",
                        "label": "Staff",
                        "access_level": 30,
                        "required": [],
                        "optional": [],
                    }
                ],
                response_only=True,
            )
        ],
    )
    @action(
        detail=False,
        methods=["get"],
        pagination_class=None,
        filter_backends=[],
    )
    def categories(self, request):
        serializer = CategorySerializer(services.list_categories(), many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="List permissions assigned to a role",
        responses={200: PermissionSerializer(many=True), 404: OpenApiTypes.OBJECT},
    )
    @action(
        detail=True,
        methods=["get"],
        pagination_class=None,
        filter_backends=[],
    )
    def permissions(self, request, slug=None):
        role = self.get_object()
        serializer = PermissionSerializer(
            [
                services.serialize_permission(permission)
                for permission in services.list_role_permissions(role)
            ],
            many=True,
        )
        return Response(serializer.data)

    @extend_schema(
        summary="Replace a role's optional permissions",
        request=RolePermissionsWriteSerializer,
        responses={
            200: PermafrostRoleSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        examples=[ROLE_EXAMPLE, VALIDATION_ERROR_EXAMPLE],
    )
    @permissions.mapping.put
    def set_permissions(self, request, slug=None):
        role = self.get_object()
        serializer = RolePermissionsWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        permissions = services.get_permissions_from_ids(
            serializer.validated_data["permission_ids"]
        )
        try:
            services.set_role_permissions(role, permissions)
        except ValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc
        return Response(PermafrostRoleSerializer(role).data)

    @extend_schema(
        summary="List users assigned to a role",
        responses={200: UserSerializer(many=True), 404: OpenApiTypes.OBJECT},
    )
    @action(detail=True, methods=["get"])
    def users(self, request, slug=None):
        role = self.get_object()
        users = services.list_role_users(role)
        user_model = get_user_model()
        username_field = user_model.USERNAME_FIELD
        field_names = {field.name for field in user_model._meta.get_fields()}

        search = request.query_params.get("search")
        if search:
            search_query = Q(**{f"{username_field}__icontains": search})
            if "email" in field_names:
                search_query |= Q(email__icontains=search)
            users = users.filter(search_query)

        ordering_map = {"id": "pk", "username": username_field}
        if "email" in field_names:
            ordering_map["email"] = "email"
        ordering = request.query_params.get("ordering", "username,id")
        order_by = []
        for requested_field in ordering.split(","):
            requested_field = requested_field.strip()
            descending = requested_field.startswith("-")
            field_name = requested_field.removeprefix("-")
            if field_name not in ordering_map:
                raise serializers.ValidationError(
                    {
                        "ordering": (
                            "Allowed fields are: " f"{', '.join(sorted(ordering_map))}."
                        )
                    }
                )
            model_field = ordering_map[field_name]
            order_by.append(f"-{model_field}" if descending else model_field)
        users = users.order_by(*order_by)

        page = self.paginate_queryset(users)
        serialized_users = [
            {
                "id": user.pk,
                "username": user.get_username(),
                "email": getattr(user, "email", ""),
            }
            for user in page
        ]
        serializer = UserSerializer(serialized_users, many=True)
        return self.get_paginated_response(serializer.data)

    @extend_schema(
        summary="Add users to a role",
        request=RoleUsersWriteSerializer,
        responses={
            200: PermafrostRoleSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        examples=[
            MEMBERSHIP_IDS_EXAMPLE,
            MEMBERSHIP_IDENTIFIERS_EXAMPLE,
            ROLE_EXAMPLE,
        ],
    )
    @users.mapping.post
    def add_users(self, request, slug=None):
        role = self.get_object()
        serializer = RoleUsersWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        users = self._get_membership_users(serializer.validated_data)
        services.add_role_users(role, users)
        return Response(PermafrostRoleSerializer(role).data)

    @extend_schema(
        operation_id="roles_users_bulk_remove",
        summary="Remove users from a role",
        request=RoleUsersWriteSerializer,
        responses={
            204: None,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        examples=[MEMBERSHIP_IDS_EXAMPLE, MEMBERSHIP_IDENTIFIERS_EXAMPLE],
    )
    @users.mapping.delete
    def remove_users(self, request, slug=None):
        role = self.get_object()
        serializer = RoleUsersWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        users = self._get_membership_users(serializer.validated_data)
        services.remove_role_users(role, users)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def _get_membership_users(validated_data):
        if "user_ids" in validated_data:
            return services.get_users_from_ids(validated_data["user_ids"])
        return services.get_users_from_identifiers(validated_data["user_identifiers"])

    @extend_schema(
        operation_id="roles_users_remove",
        summary="Remove one user from a role by primary key",
        parameters=[
            OpenApiParameter(
                "user_id",
                OpenApiTypes.INT,
                OpenApiParameter.PATH,
                description="User primary key.",
            )
        ],
        responses={204: None, 404: OpenApiTypes.OBJECT},
    )
    @action(detail=True, methods=["delete"], url_path=r"users/(?P<user_id>[^/.]+)")
    def remove_user(self, request, slug=None, user_id=None):
        role = self.get_object()
        user = get_object_or_404(get_user_model(), pk=user_id)
        services.remove_role_users(role, [user])
        return Response(status=status.HTTP_204_NO_CONTENT)
