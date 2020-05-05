from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.auth.backends import ModelBackend, AllowAllUsersModelBackend, RemoteUserBackend, AllowAllUsersRemoteUserBackend


class GroupSiteFilterMixin():

    def _get_group_permissions(self, user_obj):
        '''
        Adds the SiteID for filtering Groups
        '''
        user_groups_field = get_user_model()._meta.get_field('groups')
        user_groups_query = 'group__%s' % user_groups_field.related_query_name()
        return Permission.objects.filter(**{user_groups_query: user_obj})                   # TODO: Should it return Groups that do not have a Permafrost Role also?


class PermafrostModelBackend(GroupSiteFilterMixin, ModelBackend):
    '''
    Permafrost ModelBackend that takes into account SiteID when filtering on
    Group permissions via Permafrost Roles.
    '''
    pass


class PermafrostAllowAllUsersModelBackend(GroupSiteFilterMixin, AllowAllUsersModelBackend):
    '''
    Permafrost AllowAllUsersModelBackend that takes into account SiteID when filtering on
    Group permissions via Permafrost Roles.
    '''
    pass


class PermafrostRemoteUserBackend(GroupSiteFilterMixin, RemoteUserBackend):
    '''
    Permafrost RemoteUserBackend that takes into account SiteID when filtering on
    Group permissions via Permafrost Roles.
    '''
    pass


class PermafrostAllowAllUsersRemoteUserBackend(GroupSiteFilterMixin, AllowAllUsersRemoteUserBackend):
    '''
    Permafrost AllowAllUsersRemoteUserBackend that takes into account SiteID when filtering on
    Group permissions via Permafrost Roles.
    '''
    pass
