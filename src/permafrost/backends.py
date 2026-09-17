from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.auth.backends import (
    ModelBackend,
    AllowAllUsersModelBackend,
    RemoteUserBackend,
    AllowAllUsersRemoteUserBackend,
)
from .context import get_context_filter, get_default_context_object


class GroupSiteModelBackendMixin:

    def _get_context_group_permissions(self, user_obj, site=None, context=None):
        if not user_obj.is_active or user_obj.is_anonymous:
            return set()

        if user_obj.is_superuser:
            permissions = Permission.objects.all()
        else:
            permissions = self._get_group_permissions(
                user_obj,
                site=site,
                context=context,
            )

        return {
            f"{app_label}.{codename}"
            for app_label, codename in permissions.values_list(
                "content_type__app_label", "codename"
            ).order_by()
        }

    def _get_group_permissions(self, user_obj, obj=None, site=None, context=None):
        """
        Adds the configured Permafrost context for filtering Groups.
        """
        current_context = context or site or get_default_context_object()

        user_groups_field = get_user_model()._meta.get_field("groups")
        user_groups_query = "group__%s" % user_groups_field.related_query_name()

        return Permission.objects.filter(
            **{user_groups_query: user_obj},
            **{
                f"group__permafrost_role__{key}": value
                for key, value in get_context_filter(current_context).items()
            },
        )

    def get_group_permissions(self, user_obj, obj=None, site=None, context=None):
        """
        Return permissions for the current context without Django's user-wide
        group permission cache.

        Django's standard cache key does not contain a context identifier, so
        reusing it could grant permissions from a previously checked tenant.
        """
        if obj is not None:
            return set()
        return self._get_context_group_permissions(
            user_obj,
            site=site,
            context=context,
        )

    async def aget_group_permissions(self, user_obj, obj=None, site=None, context=None):
        return await sync_to_async(self.get_group_permissions)(
            user_obj,
            obj=obj,
            site=site,
            context=context,
        )

    def get_all_permissions(self, user_obj, obj=None, site=None, context=None):
        """Combine global user permissions with uncached context permissions."""
        if not user_obj.is_active or user_obj.is_anonymous or obj is not None:
            return set()

        return {
            *self.get_user_permissions(user_obj, obj=obj),
            *self.get_group_permissions(
                user_obj,
                obj=obj,
                site=site,
                context=context,
            ),
        }

    async def aget_all_permissions(self, user_obj, obj=None, site=None, context=None):
        if not user_obj.is_active or user_obj.is_anonymous or obj is not None:
            return set()

        return {
            *await self.aget_user_permissions(user_obj, obj=obj),
            *await self.aget_group_permissions(
                user_obj,
                obj=obj,
                site=site,
                context=context,
            ),
        }


class PermafrostModelBackend(GroupSiteModelBackendMixin, ModelBackend):
    """
    Permafrost ModelBackend that takes into account SiteID when filtering on
    Group permissions via Permafrost Roles.
    """

    pass


class PermafrostAllowAllUsersModelBackend(
    GroupSiteModelBackendMixin, AllowAllUsersModelBackend
):
    """
    Permafrost AllowAllUsersModelBackend that takes into account SiteID when filtering on
    Group permissions via Permafrost Roles.
    """

    pass


class PermafrostRemoteUserBackend(GroupSiteModelBackendMixin, RemoteUserBackend):
    """
    Permafrost RemoteUserBackend that takes into account SiteID when filtering on
    Group permissions via Permafrost Roles.
    """

    pass


class PermafrostAllowAllUsersRemoteUserBackend(
    GroupSiteModelBackendMixin, AllowAllUsersRemoteUserBackend
):
    """
    Permafrost AllowAllUsersRemoteUserBackend that takes into account SiteID when filtering on
    Group permissions via Permafrost Roles.
    """

    pass
