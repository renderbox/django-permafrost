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

class MethodPermissionRequiredMixin(PermissionRequiredMixin):
    '''
    This is a simple mixin that extend the built in PermissionRequiredMixin 
    and lets a developer specify perms required by a user either globally or in 
    order to access a particular http method.  It does a check of what the
    user has permission to do against what the view requires.  If they don't
    have the required permissions, then the user is rejected.

    Permissions can also be set per HTTP method, by appending the lowercase
    method name to 'permission_required_' and providing a set of permissions.

    permission_required = ('sites.add_site',)
    permission_required_get = ()
    permission_required_post = ()
    permission_mode = "any"/"all"     Can any permission work or are all required?
    '''

    permission_mode = "any"         # TODO: add handling of this

    def get_permission_required(self):
        """
        Override this method to override the permission_required attribute.
        Must return an iterable.
        """
        perms = super().get_permission_required()

        method_perms = getattr(self, "permission_required_" + request.method.lower(), set() )       # Extended Perms per method

        if isinstance(method_perms, str):
            method_perms = (method_perms,)

        return set(perms + method_perms)


class LogPermissionRequiredMixin(object):
    '''
    A mixin that lets you define a logger in which to write failed permission attempts to.
    '''

    no_permission_logger = None

    def handle_no_permission(self):
        
        if self.no_permission_logger is None:
            raise ImproperlyConfigured(
                '{0} is missing the no_permission_logger attribute. Define {0}.no_permission_logger'.format(self.__class__.__name__)
            )

        logger = logging.getLogger(self.no_permission_logger)

        user_ip = get_client_ip(self.request)
        user_perms = list(self.request.user.get_all_permissions())
        view_perms = list(self.get_permission_required())

        logger.info("Failed-Permission-Check:403:{0}:{1}:{2}:{3}:{4}:{5}:{6}".format(                   # Should be replaced with a Formater
                                user_ip, self.request.user.username, self.request.user.pk, 
                                self.request.method, self.request.path, ','.join(user_perms),
                                ','.join(view_perms) )
                            )

        super().handle_no_permission()
