import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseForbidden
from django.http.response import Http404
from django.shortcuts import get_object_or_404, render
from django.urls.base import reverse, reverse_lazy
from django.views.generic import TemplateView, ListView, DetailView, UpdateView, DeleteView
from unittest import skipIf

from django.views.generic.edit import CreateView, FormView

from .models import PermafrostRole
from .forms import PermafrostRoleCreateForm, PermafrostRoleUpdateForm, SelectPermafrostRoleTypeForm
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



# Create Permission Group
class PermafrostRoleCreateView(PermissionRequiredMixin, CreateView):
    model = PermafrostRole
    permission_required = ['permafrost.add_permafrostrole']

    def post(self, request, *args, **kwargs):
        if self.request.POST.get('select_role', False):
            submitted =  SelectPermafrostRoleTypeForm(request.POST)
            if submitted.is_valid():
                form = PermafrostRoleCreateForm(initial=submitted.cleaned_data)
            else:
                form = submitted
            return render(
                request, 
                'permafrost/permafrostrole_form.html', 
                context={ 'form': form },
            )

        return super().post(request, *args, **kwargs)
    
    def get_form_class(self):
        if self.request.method == 'GET':
            return SelectPermafrostRoleTypeForm
        return PermafrostRoleCreateForm



# List Permission Groups
class PermafrostRoleListView(PermissionRequiredMixin, ListView):
    model = PermafrostRole
    queryset = PermafrostRole.on_site.all()
    permission_required = ['permafrost.view_permafrostrole']

class PermafrostRoleManageView(PermafrostRoleListView):
    """
     Landing Listview with selected model for detail display
    """
    template_name = 'permafrost/permafrostrole_manage.html'

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        queryset = context['object_list']
        landing_role = queryset.first()
        
        visible_permission_ids = landing_role.all_perm_ids()
        
        context['object'] = landing_role
        
        context['permissions'] = landing_role.permissions().filter(id__in=visible_permission_ids).order_by('content_type')
        
        return context

# Detail Permission Groups
class PermafrostRoleDetailView(PermissionRequiredMixin, DetailView):
    model = PermafrostRole
    template_name = 'permafrost/permafrostrole_manage.html'
    queryset = PermafrostRole.on_site.all()
    permission_required = ['permafrost.view_permafrostrole']
    
    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        
        context['object_list'] = self.queryset
        
        role = context['object']
        visible_permission_ids = role.all_perm_ids()

        context['permissions'] = role.permissions().filter(id__in=visible_permission_ids).order_by('content_type')

        return context


# Update Permission Group
class PermafrostRoleUpdateView(PermissionRequiredMixin, UpdateView):
    template_name = 'permafrost/permafrostrole_form.html'
    form_class = PermafrostRoleUpdateForm
    model = PermafrostRole
    queryset = PermafrostRole.on_site.all()
    permission_required = ['permafrost.change_permafrostrole']

# Delete Permission Groups
class PermafrostRoleDeleteView(DeleteView):
    model = PermafrostRole


# Future Views

# TODO: Role User List (For easier pagination) & bulk editing

# TODO: User Roles on a given Site

# TODO: Roles with a given permission
