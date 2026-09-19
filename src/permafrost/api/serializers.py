from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import ValidationError as DjangoValidationError

from permafrost.api import services

try:
    from drf_spectacular.utils import extend_schema_field
    from rest_framework import serializers
except ImportError as exc:
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured(
        "Django REST Framework and drf-spectacular are required to use "
        "permafrost.api.serializers. Install django-permafrost[api] to enable "
        "the Permafrost HTTP API."
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

    @extend_schema_field(PermissionSerializer(many=True))
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

    def validate_permission_ids(self, value):
        try:
            services.get_permissions_from_ids(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                exc.message_dict["permission_ids"][0]
            ) from exc
        return value

    def validate(self, attrs):
        if self.instance is not None:
            requested_category = attrs.get("category")
            if (
                requested_category is not None
                and requested_category != self.instance.category
            ):
                raise serializers.ValidationError(
                    {"category": "Role category cannot be changed."}
                )
            attrs.pop("category", None)
        return attrs

    def create(self, validated_data):
        permission_ids = validated_data.pop("permission_ids", None)
        permissions = None
        if permission_ids is not None:
            permissions = services.get_permissions_from_ids(permission_ids)
        try:
            return services.create_role(
                permissions=permissions,
                request=self.context.get("request"),
                **validated_data,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc

    def update(self, instance, validated_data):
        permission_ids = validated_data.pop("permission_ids", None)
        permissions = None
        if permission_ids is not None:
            permissions = services.get_permissions_from_ids(permission_ids)
        try:
            return services.update_role(
                instance, permissions=permissions, **validated_data
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc


class RolePermissionsWriteSerializer(serializers.Serializer):
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(), required=True, allow_empty=True
    )

    def validate_permission_ids(self, value):
        try:
            services.get_permissions_from_ids(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                exc.message_dict["permission_ids"][0]
            ) from exc
        return value


class RoleUsersWriteSerializer(serializers.Serializer):
    user_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, allow_empty=False
    )
    user_identifiers = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=False
    )

    def validate(self, attrs):
        supplied_fields = {
            field_name
            for field_name in ("user_ids", "user_identifiers")
            if field_name in attrs
        }
        if len(supplied_fields) != 1:
            raise serializers.ValidationError(
                "Supply exactly one of user_ids or user_identifiers."
            )

        try:
            if "user_ids" in attrs:
                services.get_users_from_ids(attrs["user_ids"])
            else:
                services.get_users_from_identifiers(attrs["user_identifiers"])
        except (DjangoValidationError, ImproperlyConfigured) as exc:
            if isinstance(exc, DjangoValidationError):
                detail = exc.message_dict
            else:
                detail = {"user_identifiers": str(exc)}
            raise serializers.ValidationError(detail) from exc
        return attrs
