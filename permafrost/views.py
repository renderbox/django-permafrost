import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView

#--------------
# UTILITIES
#--------------

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


#--------------
# MIXIN VIEWS
#--------------

class PermafrostMixin(PermissionRequiredMixin):
    '''
    This is a simple mixin that extend the built in PermissionRequiredMixin 
    and lets a developer specify perms required by a user for a particular 
    http method.  For example, a user with a 'get' pemission might not be
    given permissions to reach a 'post' endpoint in the view.
    
    If they don't have the required permissions, then the user
    is rejected.

    Permissions can be set per HTTP method, by appending the lowercase
    method name to 'permission_required_' and providing a set of permissions.

    permission_required = ('sites.add_site',)
    permission_required_get = ()
    permission_required_post = ()
    '''

    def get_permission_required(self):
        """
        Override this method to override the permission_required attribute.
        Must return an iterable.
        """
        perms = super().get_permission_required()

        method_perms = getattr(self, "permission_required_" + self.request.method.lower(), set() )       # Extended Perms per method

        if isinstance(method_perms, str):
            method_perms = (method_perms,)

        return set(list(perms) + list(method_perms))


class PermafrostLogMixin(object):
    '''
    A mixin that lets you define a logger in which to write failed permission attempts to.
    '''

    permission_logger = None

    def handle_no_permission(self):
        
        if self.permission_logger is None:  # TODO Make this assume a default logger called "permafrost"
            raise ImproperlyConfigured(
                '{0} is missing the permission_logger attribute. Define {0}.permission_logger'.format(self.__class__.__name__)
            )

        logger = logging.getLogger(self.permission_logger)

        user_ip = get_client_ip(self.request)
        user_perms = list(self.request.user.get_all_permissions())
        view_perms = list(self.get_permission_required())

        logger.info("Failed-Permission-Check:403:{0}:{1}:{2}:{3}:{4}:{5}:{6}".format(                   # Should be replaced with a Formater
                                user_ip, self.request.user.username, self.request.user.pk, 
                                self.request.method, self.request.path, ','.join(user_perms),
                                ','.join(view_perms) )
                            )

        super().handle_no_permission()


#--------------
# DJANGO REST PERMS
#--------------

try:
    from rest_framework.permission import BasePermission

    class PermafrostRESTPermission(BasePermission):

        def has_permission(self, request, view):
            perms = getattr(view, "permission_required", set() )
            method_perms = getattr(view, "permission_required_" + self.request.method.lower(), set() )

            check_list = list(perms) + list(method_perms)
            user_perms = request.user.get_all_permissions()

            # Get the user's perms and check that all the itms in the list are present
            for perm in check_list:
                if perm not in user_perms:
                    return False

            return True

except ModuleNotFoundError:
    pass