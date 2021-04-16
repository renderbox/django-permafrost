import logging

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.views.generic import (
    ListView,
    DetailView,
    UpdateView,
    DeleteView,
)

from django.views.generic.edit import CreateView

from .models import PermafrostRole, get_optional_by_category, get_required_by_category
from .forms import (
    PermafrostRoleCreateForm,
    PermafrostRoleUpdateForm,
    SelectPermafrostRoleTypeForm,
)

from .permissions import has_all_permissions

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
            return PermafrostRole.objects.filter(site=self.request.site)
        return super().get_queryset()

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
                    kwargs['site'] = request.site
                
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

        visible_permission_ids = landing_role.all_perm_ids()

        context["object"] = landing_role

        context["permissions"] = (
            landing_role.permissions()
            .filter(id__in=visible_permission_ids)
            .order_by("content_type")
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

        context["object_list"] = self.queryset

        role = context["object"]
        visible_permission_ids = role.all_perm_ids()

        context["permissions"] = (
            role.permissions()
            .filter(id__in=visible_permission_ids)
            .order_by("content_type")
        )

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
class PermafrostRoleDeleteView(DeleteView):
    model = PermafrostRole


# Future Views

# TODO: Role User List (For easier pagination) & bulk editing

# TODO: User Roles on a given Site

# TODO: Roles with a given permission
