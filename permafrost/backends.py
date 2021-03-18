from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.auth.backends import ModelBackend, AllowAllUsersModelBackend, RemoteUserBackend, AllowAllUsersRemoteUserBackend
from django.contrib.sites.models import Site

class GroupSiteModelBackendMixin():

    def _get_group_permissions(self, user_obj, obj=None, site=None):
        '''
        Adds the SiteID for filtering Groups
        '''
        if site:
            current_site = site
        else:
            current_site = Site.objects.get_current()
    
        user_groups_field = get_user_model()._meta.get_field('groups')
        user_groups_query = 'group__%s' % user_groups_field.related_query_name()

        return Permission.objects.filter(**{user_groups_query: user_obj}, group__permafrost_role__site=current_site)                   # TODO: Should it return Groups that do not have a Permafrost Role also?


class PermafrostModelBackend(GroupSiteModelBackendMixin, ModelBackend):
    '''
    Permafrost ModelBackend that takes into account SiteID when filtering on
    Group permissions via Permafrost Roles.
    '''
    pass


class PermafrostAllowAllUsersModelBackend(GroupSiteModelBackendMixin, AllowAllUsersModelBackend):
    '''
    Permafrost AllowAllUsersModelBackend that takes into account SiteID when filtering on
    Group permissions via Permafrost Roles.
    '''
    pass


class PermafrostRemoteUserBackend(GroupSiteModelBackendMixin, RemoteUserBackend):
    '''
    Permafrost RemoteUserBackend that takes into account SiteID when filtering on
    Group permissions via Permafrost Roles.
    '''
    pass


class PermafrostAllowAllUsersRemoteUserBackend(GroupSiteModelBackendMixin, AllowAllUsersRemoteUserBackend):
    '''
    Permafrost AllowAllUsersRemoteUserBackend that takes into account SiteID when filtering on
    Group permissions via Permafrost Roles.
    '''
    pass
