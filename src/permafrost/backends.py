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
