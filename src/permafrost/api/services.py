from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError

from permafrost.context import get_context_filter, get_request_context_object
from permafrost.models import (
    CATEGORIES,
    PERMAFROST_EXCLUDED_ROLES,
    PermafrostRole,
    get_optional_by_category,
    get_required_by_category,
)


def get_context_object(request=None, context_object=None):
    if context_object is not None:
        return context_object
    if request is not None:
        return get_request_context_object(request)
    return None


def get_role_queryset(
    request=None,
    context_object=None,
    include_deleted=False,
    include_excluded=False,
):
    context_object = get_context_object(request=request, context_object=context_object)
    queryset = PermafrostRole.objects.all()

    if context_object is not None:
        queryset = queryset.filter(**get_context_filter(context_object))

    if not include_deleted:
        queryset = queryset.filter(deleted=False)

    if not include_excluded:
        queryset = queryset.exclude(name__in=PERMAFROST_EXCLUDED_ROLES)

    return queryset


def list_roles(*args, **kwargs):
    return get_role_queryset(*args, **kwargs)


def get_role(slug, request=None, context_object=None, include_deleted=False):
    return get_role_queryset(
        request=request,
        context_object=context_object,
        include_deleted=include_deleted,
    ).get(slug=slug)


def serialize_permission(permission):
    return {
        "id": permission.pk,
        "name": permission.name,
        "codename": permission.codename,
        "app_label": permission.content_type.app_label,
        "model": permission.content_type.model,
        "natural_key": permission.natural_key(),
    }


def list_categories():
    categories = []
    for key, data in CATEGORIES.items():
        categories.append(
            {
                "key": key,
                "label": data.get("label", key),
                "access_level": data.get("access_level", data.get("level")),
                "required": [
                    serialize_permission(permission)
                    for permission in get_required_by_category(key)
                ],
                "optional": [
                    serialize_permission(permission)
                    for permission in get_optional_by_category(key)
                ],
            }
        )
    return categories


def validate_category(category):
    if category not in CATEGORIES:
        raise ValidationError({"category": "Unknown Permafrost role category."})
    return category


def get_permissions_from_ids(permission_ids):
    permission_ids = permission_ids or []
    return Permission.objects.filter(id__in=permission_ids)


def create_role(
    *,
    name,
    category,
    description="",
    permissions=None,
    request=None,
    context_object=None,
    locked=False,
):
    validate_category(category)
    context_object = get_context_object(request=request, context_object=context_object)

    role = PermafrostRole(
        name=name,
        description=description,
        category=category,
        locked=locked,
    )
    if context_object is not None:
        role.set_context(context_object)
    role.save()

    if permissions is not None:
        role.permissions_set(permissions)

    return role


def update_role(
    role,
    *,
    name=None,
    description=None,
    permissions=None,
    deleted=None,
):
    if name is not None:
        role.name = name
    if description is not None:
        role.description = description
    if deleted is not None and not role.locked and not role.is_default_role():
        role.deleted = deleted

    role.save()

    if permissions is not None:
        role.permissions_set(permissions)

    return role


def set_role_permissions(role, permissions):
    role.permissions_set(permissions)
    return role


def add_role_permissions(role, permissions):
    role.permissions_add(*permissions)
    return role


def remove_role_permissions(role, permissions):
    role.permissions_remove(*permissions)
    return role


def list_role_permissions(role):
    return role.permissions().all()


def list_role_users(role):
    return role.user_set()


def get_users_from_ids(user_ids):
    user_ids = user_ids or []
    return get_user_model().objects.filter(id__in=user_ids)


def add_role_users(role, users):
    role.users_add(*users)
    return role


def remove_role_users(role, users):
    role.users_remove(*users)
    return role


def delete_role(role, soft=True):
    if soft:
        return update_role(role, deleted=True)
    role.delete()
    return role
