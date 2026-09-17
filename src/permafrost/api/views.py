from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404

from permafrost.api import services

try:
    from rest_framework import filters, serializers, status, viewsets
    from rest_framework.decorators import action
    from rest_framework.response import Response
except ImportError as exc:
    raise ImproperlyConfigured(
        "Django REST Framework is required to use permafrost.api.views. "
        "Install djangorestframework to enable the Permafrost HTTP API."
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


class PermafrostRoleViewSet(viewsets.ModelViewSet):
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

    @action(detail=False, methods=["get"])
    def categories(self, request):
        serializer = CategorySerializer(services.list_categories(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
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

    @users.mapping.post
    def add_users(self, request, slug=None):
        role = self.get_object()
        serializer = RoleUsersWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        users = services.get_users_from_ids(serializer.validated_data["user_ids"])
        services.add_role_users(role, users)
        return Response(PermafrostRoleSerializer(role).data)

    @action(detail=True, methods=["delete"], url_path=r"users/(?P<user_id>[^/.]+)")
    def remove_user(self, request, slug=None, user_id=None):
        role = self.get_object()
        user = get_object_or_404(get_user_model(), pk=user_id)
        services.remove_role_users(role, [user])
        return Response(status=status.HTTP_204_NO_CONTENT)
