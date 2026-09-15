from django.core.exceptions import ImproperlyConfigured

from permafrost.permissions import has_all_permissions

try:
    from rest_framework.permissions import BasePermission
except ImportError as exc:
    raise ImproperlyConfigured(
        "Django REST Framework is required to use permafrost.api.permissions. "
        "Install djangorestframework to enable the Permafrost HTTP API."
    ) from exc


class PermafrostAPIPermission(BasePermission):
    perms_map = {
        "list": ["permafrost.view_permafrostrole"],
        "retrieve": ["permafrost.view_permafrostrole"],
        "create": ["permafrost.add_permafrostrole"],
        "update": ["permafrost.change_permafrostrole"],
        "partial_update": ["permafrost.change_permafrostrole"],
        "destroy": ["permafrost.delete_permafrostrole"],
        "categories": ["permafrost.view_permafrostrole"],
        "permissions": ["permafrost.view_permafrostrole"],
        "set_permissions": ["permafrost.change_permafrostrole"],
        "users": ["permafrost.view_permafrostrole"],
        "add_users": ["permafrost.add_user_to_role"],
        "remove_user": ["permafrost.add_user_to_role"],
    }

    def has_permission(self, request, view):
        required = getattr(view, "permission_required", None)
        if required is None:
            required = self.perms_map.get(getattr(view, "action", None), [])
        return has_all_permissions(request, required)
