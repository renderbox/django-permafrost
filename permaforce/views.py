import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView

security_logger = logging.getLogger('security')

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

class PermCheckMixin(object):
    '''
    This is a simple mixin that lets a user specify perms required by a
    user either globally or in order to access a particular http method.  It
    does a check of what the user has permission to do against what the view
    requires.  If they don't intersect, then the user is rejected.

    401 -> Non-Logged in users      return HttpResponse('Unauthorized', status=401)
    403 -> Logged in users          return HttpResponseForbidden()

    Perms can also be set per HTTP method, by appending the lowercase
    method name to 'perms_' and providing a list of perms.

    perms = []
    perms_get = []
    perms_post = []

    permission naming convention:

        <role_category>_<perm_group>_do_something

        faculty_student_edit_profile

    There is support for checking modes:

        any -> Any match will work
        all -> The user needs to match all the perms (perms and
                perms_<method>).
    '''
    perms = []
    mode = "any"

    def dispatch(self, request, *args, **kwargs):

        result = super().dispatch(request, *args, **kwargs)
        user_ip = get_client_ip(request)

        try:
            view_perms = self.get_perms(request) #set(self.perms + getattr(self, "perms_" + request.method.lower(), [] ))
            user_perms = request.user.perms()     # todo: Move this to the session variable and update it with Signals on login and change.

            # if view_perms and request.user.is_authenticated:   # If there are any perms to check, check them, otherwise pass by default
            if view_perms:   # If there are any perms to check, check them, otherwise pass by default
                valid = False       # Default to fail check if perms are provided
                intersect = view_perms.intersection(user_perms)

                if self.mode == "any":
                    valid = bool( intersect )                 # Returns True if there is anything in the Set
                if self.mode == "all":
                    valid = bool( view_perms == intersect )   # Returns True if the view_perms match the intersection with the user

                if not valid:
                    if request.user.is_authenticated:
                        security_logger.info("Failed-Permission-Check:403:{0}:{1}:{2}:{3}:{4}:{5}:{6}".format(
                                                        user_ip,
                                                        request.user.username, 
                                                        request.user.pk, 
                                                        request.method, 
                                                        request.path,
                                                        ','.join(user_perms),
                                                        ','.join(view_perms)
                                                        )
                                            )
                        return HttpResponseForbidden('<h1>403 Forbidden</h1><p>You do not have permission to access this resource on this server</p>', content_type='text/html')
                    else:
                        security_logger.info("Failed-Permission-Check:401:ANNONYMOUS:None:{0}:{1}:{2}:{3}".format(
                                user_ip,
                                request.method, 
                                request.path,
                                ','.join(view_perms)))

                        return HttpResponse('Unauthorized', status=401)

        except AttributeError:
            security_logger.info("Failed-Permission-Check:401:ANNONYMOUS:None:{0}:{1}:{2}:{3}".format(
                    user_ip,
                    request.method, 
                    request.path,
                    ','.join(view_perms)))

            return HttpResponse('Unauthorized', status=401)

        return result

    @classmethod
    def get_perms(cls, request):
        '''
        Class method so its perms can be checked without having to instatiate the view.
        '''
        return set(cls.perms + getattr(cls, "perms_" + request.method.lower(), [] ))
