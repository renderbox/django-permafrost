import logging
from django.urls import reverse_lazy
from django.contrib.auth.models import Permission
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.views.generic import (
    ListView,
    DetailView,
    UpdateView,
    DeleteView,
)
from django.db.models import Q
from django.views.generic.edit import CreateView

from .models import PermafrostRole, get_optional_by_category, get_required_by_category, get_all_perms_for_all_categories
from .forms import (
    PermafrostRoleCreateForm,
    PermafrostRoleUpdateForm,
    SelectPermafrostRoleTypeForm,
)
from django.http import HttpResponseBadRequest, HttpResponse, HttpResponseNotFound
from .permissions import has_all_permissions
from django.middleware.csrf import get_token
from django.contrib.sites.models import Site

# --------------
# UTILITIES
# --------------


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def group_permission_categories(required, optional, selected_optional):
    permission_categories = {}
    for permission in set(required + optional):
        permission_type_key = "required" if permission in required else "optional"
        if permission.content_type.model not in permission_categories:
            permission_categories[permission.content_type.model] = {
                "name": permission.content_type.name,
                "optional": [],
                "required": [],
            }
        if permission in selected_optional:
            permission.selected = True
        permission_categories[permission.content_type.model][
            permission_type_key
        ].append(permission)
    return permission_categories


# --------------
# MIXIN VIEWS
# --------------


class PermafrostMixin(PermissionRequiredMixin):
    """
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
    """

    def get_permission_required(self):
        """
        Override this method to override the permission_required attribute.
        Must return an iterable.
        """
        perms = super().get_permission_required()

        method_perms = getattr(
            self, "permission_required_" + self.request.method.lower(), set()
        )  # Extended Perms per method

        if isinstance(method_perms, str):
            method_perms = (method_perms,)

        return set(list(perms) + list(method_perms))

class PermafrostSiteMixin(PermafrostMixin):
    """
    This mixin can be added to a View to create a new method for retrieving permissions for users based on their per-site permafrost roles using request.site rather than SITE_ID.
    """
    def has_permission(self):
        
        check_list = self.get_permission_required()
        
        return has_all_permissions(self.request, check_list)
        

class PermafrostLogMixin(object):
    """
    A mixin that lets you define a logger in which to write failed permission attempts to.
    """

    permission_logger = None

    def handle_no_permission(self):

        if (
            self.permission_logger is None
        ):  # TODO Make this assume a default logger called "permafrost"
            raise ImproperlyConfigured(
                "{0} is missing the permission_logger attribute. Define {0}.permission_logger".format(
                    self.__class__.__name__
                )
            )

        logger = logging.getLogger(self.permission_logger)

        user_ip = get_client_ip(self.request)
        user_perms = list(self.request.user.get_all_permissions())
        view_perms = list(self.get_permission_required())

        logger.info(
            "Failed-Permission-Check:403:{0}:{1}:{2}:{3}:{4}:{5}:{6}".format(  # Should be replaced with a Formater
                user_ip,
                self.request.user.username,
                self.request.user.pk,
                self.request.method,
                self.request.path,
                ",".join(user_perms),
                ",".join(view_perms),
            )
        )

        super().handle_no_permission()

class FilterByRequestSiteQuerysetMixin:
    def get_queryset(self):
        if hasattr(self.request, 'site'):
            return PermafrostRole.objects.filter(site=self.request.site, deleted=False)
        return super().get_queryset()

class GetRoleExternalPermissionsMixin:
    def get_perms_excluding_current_role(self, context):
        role = context['object']
        required = role.required_permissions()
        optional = role.optional_permissions()
        selected = list(role.permissions().all())
        all_perms = get_all_perms_for_all_categories()
        perms_excluding_current_role = list(set(all_perms) - set(required + optional + selected))
        return perms_excluding_current_role

# Create Permission Group
class PermafrostRoleCreateView(PermafrostSiteMixin, CreateView):
    model = PermafrostRole
    permission_required = ["permafrost.add_permafrostrole"]

    def post(self, request, *args, **kwargs):
        if self.request.POST.get("select_role", False):
            submitted = SelectPermafrostRoleTypeForm(request.POST)
            permission_categories = {}
            if submitted.is_valid():

                kwargs = {'initial': submitted.cleaned_data}
                if hasattr(request, 'site'):
                    kwargs['site'] = self.request.site
                
                form = PermafrostRoleCreateForm(**kwargs)
                category = submitted.cleaned_data["category"]
                required = get_required_by_category(category=category)
                optional = get_optional_by_category(category=category)
                selected_optional = []
                permission_categories = group_permission_categories(
                    required, optional, selected_optional
                )
            else:
                form = submitted
            return render(
                request,
                "permafrost/permafrostrole_form.html",
                context={"form": form, "permission_categories": permission_categories},
            )

        return super().post(request, *args, **kwargs)

    def get_form_class(self):
        if self.request.method == "GET":
            return SelectPermafrostRoleTypeForm
        return PermafrostRoleCreateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.get_form_class() == PermafrostRoleCreateForm:
            if hasattr(self.request, 'site'):
                kwargs['site'] = self.request.site
        return kwargs

# List Permission Groups
class PermafrostRoleListView(PermafrostSiteMixin, FilterByRequestSiteQuerysetMixin, ListView):
    model = PermafrostRole
    queryset = PermafrostRole.on_site.all()
    permission_required = ["permafrost.view_permafrostrole"]
    
class PermafrostRoleManageView(PermafrostRoleListView):
    """
    Landing Listview with selected model for detail display
    """

    template_name = "permafrost/permafrostrole_manage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = context["object_list"]
        landing_role = queryset.first()

        if landing_role:
            visible_permission_ids = landing_role.all_perm_ids()

            context["object"] = landing_role

            context["permissions"] = (
                landing_role.permissions()
                .filter(id__in=visible_permission_ids)
                .order_by("content_type").distinct()
            )

        return context


# Detail Permission Groups
class PermafrostRoleDetailView(PermafrostSiteMixin, FilterByRequestSiteQuerysetMixin, DetailView):
    model = PermafrostRole
    template_name = "permafrost/permafrostrole_manage.html"
    queryset = PermafrostRole.on_site.all()
    permission_required = ["permafrost.view_permafrostrole"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["object_list"] = self.get_queryset()

        role = context["object"]
        context['permissions'] = role.permissions().all().order_by("content_type").distinct()
        return context


# Update Permission Group
class PermafrostRoleUpdateView(PermafrostSiteMixin, FilterByRequestSiteQuerysetMixin, UpdateView):
    template_name = "permafrost/permafrostrole_form.html"
    form_class = PermafrostRoleUpdateForm
    model = PermafrostRole
    queryset = PermafrostRole.on_site.all()
    permission_required = ["permafrost.change_permafrostrole"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role = context["object"]
        required = role.required_permissions()
        optional = role.optional_permissions()
        other = list(role.permissions().all())
        optional = list(set(optional + other))
        selected_optional = role.permissions().filter(
            id__in=[permission.id for permission in optional]
        )
        context["permission_categories"] = group_permission_categories(
            required, optional, selected_optional
        )
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request, 'site'):
            kwargs['site'] = self.request.site
        return kwargs

# Delete Permission Groups
class PermafrostRoleDeleteView(PermafrostSiteMixin, FilterByRequestSiteQuerysetMixin, DeleteView):
    model = PermafrostRole
    success_url = reverse_lazy('permafrost:roles-manage')  
    permission_required = ["permafrost.delete_permafrostrole"]


# Custom Role Modal View
class PermafrostCustomRoleModalView(PermafrostSiteMixin, FilterByRequestSiteQuerysetMixin, GetRoleExternalPermissionsMixin, DetailView):
    model = PermafrostRole
    template_name = "permafrost/permissions_modal.html"
    permission_required = ["permafrost.change_permafrostrole"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        perms_excluding_current_role = self.get_perms_excluding_current_role(context)
        query = self.request.GET.get('q', None)
        
        if query:
            # perform search filtering
            perms_pks = [perm.pk for perm in perms_excluding_current_role]
            filter1 = Q(name__icontains=query)
            #filter2 = Q(content_type__name__icontains=query) # TODO why does this filter not work?
            # @fahzee1 tried adding the filter back, i think because name is an @property on the model and not a db column
            perms_queryset = Permission.objects.filter(pk__in=perms_pks)
            perms_to_group = list(perms_queryset.filter(filter1))
        else:
            perms_to_group = perms_excluding_current_role
        
        context["permission_categories"] = group_permission_categories([], perms_to_group, [])
        return context
    
    def get_template_names(self):
        if self.request.GET.get('q') == None:
            return super().get_template_names()
        return ['permafrost/includes/permissions_table.html']
   
    def post(self, request, slug, *args, **kwargs):
        current_site = getattr(request, 'site', Site.objects.get_current())
        role = PermafrostRole.objects.filter(site=current_site, slug=slug).last()
        perms_to_add = self.get_permissions_queryset()
        if perms_to_add:
            role.group.permissions.add(*perms_to_add)
        return redirect('permafrost:role-update', slug=slug)
    
    def get_permissions_queryset(self):
        permission_ids = self.request.POST.getlist('permissions', [])
        if permission_ids:
            return Permission.objects.filter(id__in=permission_ids)
        return None
# Future Views

# TODO: Role User List (For easier pagination) & bulk editing

# TODO: User Roles on a given Site

# TODO: Roles with a given permission
