from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.shortcuts import get_object_or_404

from permafrost.api import services

try:
    from rest_framework import serializers, status, viewsets
    from rest_framework.decorators import action
    from rest_framework.response import Response
except ImportError as exc:
    raise ImproperlyConfigured(
        "Django REST Framework is required to use permafrost.api.views. "
        "Install djangorestframework to enable the Permafrost HTTP API."
    ) from exc

from permafrost.api.permissions import PermafrostAPIPermission
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

    def get_queryset(self):
        return services.list_roles(request=self.request).order_by("name")

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
        serializer = UserSerializer(
            [
                {
                    "id": user.pk,
                    "username": user.get_username(),
                    "email": user.email,
                }
                for user in services.list_role_users(role)
            ],
            many=True,
        )
        return Response(serializer.data)

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
