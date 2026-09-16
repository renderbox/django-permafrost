from django.core.exceptions import ValidationError as DjangoValidationError

from permafrost.api import services

try:
    from rest_framework import serializers
except ImportError as exc:
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured(
        "Django REST Framework is required to use permafrost.api.serializers. "
        "Install djangorestframework to enable the Permafrost HTTP API."
    ) from exc


class PermissionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    codename = serializers.CharField()
    app_label = serializers.CharField()
    model = serializers.CharField()
    natural_key = serializers.ListField(child=serializers.CharField())


class CategorySerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    access_level = serializers.IntegerField(required=False, allow_null=True)
    required = PermissionSerializer(many=True)
    optional = PermissionSerializer(many=True)


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField(allow_blank=True)


class PermafrostRoleSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    slug = serializers.SlugField(read_only=True)
    description = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    category = serializers.CharField()
    locked = serializers.BooleanField(read_only=True)
    deleted = serializers.BooleanField(read_only=True)
    permissions = serializers.SerializerMethodField()

    def get_permissions(self, role):
        return [
            services.serialize_permission(permission)
            for permission in services.list_role_permissions(role)
        ]


class PermafrostRoleWriteSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    description = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    category = serializers.CharField(required=True)
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, allow_empty=True
    )

    def validate_category(self, value):
        try:
            return services.validate_category(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict["category"][0]) from exc

    def create(self, validated_data):
        permission_ids = validated_data.pop("permission_ids", None)
        permissions = None
        if permission_ids is not None:
            permissions = services.get_permissions_from_ids(permission_ids)
        return services.create_role(
            permissions=permissions,
            request=self.context.get("request"),
            **validated_data,
        )

    def update(self, instance, validated_data):
        permission_ids = validated_data.pop("permission_ids", None)
        permissions = None
        if permission_ids is not None:
            permissions = services.get_permissions_from_ids(permission_ids)
        return services.update_role(instance, permissions=permissions, **validated_data)


class RolePermissionsWriteSerializer(serializers.Serializer):
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(), required=True, allow_empty=True
    )


class RoleUsersWriteSerializer(serializers.Serializer):
    user_ids = serializers.ListField(
        child=serializers.IntegerField(), required=True, allow_empty=False
    )
