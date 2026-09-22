import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Permission
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from django.views.generic import (
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)
from django.views.generic.edit import CreateView

from .api import services
from .context import get_context_filter, get_request_context_object
from .forms import (
    PermafrostRoleCreateForm,
    PermafrostRoleUpdateForm,
    PermissionRoleLookupForm,
    RoleListFilterForm,
    RoleMembershipAddForm,
    RoleMembershipRemoveForm,
    SelectPermafrostRoleTypeForm,
    UserRoleLookupForm,
)
from .models import (
    PERMAFROST_EXCLUDED_ROLES,
    PermafrostRole,
    get_all_perms_for_all_categories,
    get_optional_by_category,
    get_required_by_category,
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
        context_object = get_request_context_object(self.request)
        return PermafrostRole.objects.filter(
            **get_context_filter(context_object), deleted=False
        )


class GetRoleExternalPermissionsMixin:
    def get_perms_excluding_current_role(self, context):
        role = context["object"]
        required = role.required_permissions()
        optional = role.optional_permissions()
        selected = list(role.permissions().all())
        all_perms = get_all_perms_for_all_categories()
        perms_excluding_current_role = list(
            set(all_perms) - set(required + optional + selected)
        )
        return perms_excluding_current_role


class RoleListContextMixin:
    """Filter and paginate the role navigation without changing tenant scope."""

    def get_role_filter_form(self):
        if not hasattr(self, "_role_filter_form"):
            self._role_filter_form = RoleListFilterForm(self.request.GET or None)
        return self._role_filter_form

    def filter_role_list(self, queryset):
        form = self.get_role_filter_form()
        if form.is_valid():
            query = form.cleaned_data["q"].strip()
            category = form.cleaned_data["category"]
            if query:
                queryset = queryset.filter(
                    Q(name__icontains=query)
                    | Q(slug__icontains=query)
                    | Q(description__icontains=query)
                )
            if category:
                queryset = queryset.filter(category=category)
        return queryset.order_by("pk")

    def get_role_list_query(self):
        query = self.request.GET.copy()
        query.pop("page", None)
        return query.urlencode()

    def add_role_list_context(self, context):
        context["role_filter_form"] = self.get_role_filter_form()
        context["role_list_query"] = self.get_role_list_query()
        context["role_list_url_query"] = self.request.GET.urlencode()
        return context


# Create Permission Group
class PermafrostRoleCreateView(PermafrostSiteMixin, CreateView):
    model = PermafrostRole
    permission_required = ["permafrost.add_permafrostrole"]

    def post(self, request, *args, **kwargs):
        if self.request.POST.get("select_role", False):
            submitted = SelectPermafrostRoleTypeForm(request.POST)
            permission_categories = {}
            if submitted.is_valid():

                kwargs = {"initial": submitted.cleaned_data}
                kwargs["context_object"] = get_request_context_object(request)

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
            if hasattr(self.request, "site"):
                kwargs["context_object"] = get_request_context_object(self.request)
        return kwargs


# List Permission Groups
class PermafrostRoleListView(
    RoleListContextMixin,
    PermafrostSiteMixin,
    FilterByRequestSiteQuerysetMixin,
    ListView,
):
    model = PermafrostRole
    queryset = PermafrostRole.on_site.all()
    permission_required = ["permafrost.view_permafrostrole"]

    def get_paginate_by(self, queryset):
        return getattr(settings, "PERMAFROST_UI_PAGE_SIZE", 50)

    def get_queryset(self):
        qs = super(PermafrostRoleListView, self).get_queryset()
        # Should be reflected in TC
        qs = qs.exclude(name__in=PERMAFROST_EXCLUDED_ROLES)
        return self.filter_role_list(qs)

    def get_context_data(self, **kwargs):
        return self.add_role_list_context(super().get_context_data(**kwargs))


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
                .order_by("content_type")
                .distinct()
            )

        return context


# Detail Permission Groups
class PermafrostRoleDetailView(
    RoleListContextMixin,
    PermafrostSiteMixin,
    FilterByRequestSiteQuerysetMixin,
    DetailView,
):
    model = PermafrostRole
    template_name = "permafrost/permafrostrole_manage.html"
    queryset = PermafrostRole.on_site.all()
    permission_required = ["permafrost.view_permafrostrole"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        role_list = self.filter_role_list(self.get_queryset())
        paginator = Paginator(
            role_list, getattr(settings, "PERMAFROST_UI_PAGE_SIZE", 50)
        )
        page_obj = paginator.get_page(self.request.GET.get("page"))
        context.update(
            {
                "object_list": page_obj.object_list,
                "page_obj": page_obj,
                "paginator": paginator,
                "is_paginated": page_obj.has_other_pages(),
            }
        )
        self.add_role_list_context(context)

        role = context["object"]
        context["permissions"] = (
            role.permissions().all().order_by("content_type").distinct()
        )
        return context

    def get_queryset(self):
        qs = super(PermafrostRoleDetailView, self).get_queryset()
        # Should be reflected in TC
        return qs.exclude(name__in=PERMAFROST_EXCLUDED_ROLES)


# Update Permission Group
class PermafrostRoleUpdateView(
    PermafrostSiteMixin, FilterByRequestSiteQuerysetMixin, UpdateView
):
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
        kwargs["context_object"] = get_request_context_object(self.request)
        return kwargs


# Delete Permission Groups
class PermafrostRoleDeleteView(
    PermafrostSiteMixin, FilterByRequestSiteQuerysetMixin, DeleteView
):
    model = PermafrostRole
    success_url = reverse_lazy("permafrost:roles-manage")
    permission_required = ["permafrost.delete_permafrostrole"]


# Custom Role Modal View
class PermafrostCustomRoleModalView(
    PermafrostSiteMixin,
    FilterByRequestSiteQuerysetMixin,
    GetRoleExternalPermissionsMixin,
    DetailView,
):
    model = PermafrostRole
    template_name = "permafrost/permissions_modal.html"
    permission_required = ["permafrost.change_permafrostrole"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        perms_excluding_current_role = self.get_perms_excluding_current_role(context)
        query = self.request.GET.get("q", None)

        if query:
            # perform search filtering
            perms_pks = [perm.pk for perm in perms_excluding_current_role]
            filter1 = Q(name__icontains=query)
            # filter2 = Q(content_type__name__icontains=query) # TODO why does this filter not work?
            # @fahzee1 tried adding the filter back, i think because name is an @property on the model and not a db column
            perms_queryset = Permission.objects.filter(pk__in=perms_pks)
            perms_to_group = list(perms_queryset.filter(filter1))
        else:
            perms_to_group = perms_excluding_current_role

        context["permission_categories"] = group_permission_categories(
            [], perms_to_group, []
        )
        return context

    def get_template_names(self):
        if self.request.GET.get("q") is None:
            return super().get_template_names()
        return ["permafrost/includes/permissions_table.html"]

    def post(self, request, slug, *args, **kwargs):
        context_object = get_request_context_object(request)
        role = PermafrostRole.objects.filter(
            **get_context_filter(context_object), slug=slug
        ).last()
        perms_to_add = self.get_permissions_queryset()
        if role and perms_to_add:
            role.permissions_add(*perms_to_add)
        return redirect("permafrost:role-update", slug=slug)

    def get_permissions_queryset(self):
        permission_ids = self.request.POST.getlist("permissions", [])
        if permission_ids:
            return Permission.objects.filter(id__in=permission_ids)
        return None


class PermafrostRoleUsersView(
    PermafrostSiteMixin, FilterByRequestSiteQuerysetMixin, DetailView
):
    model = PermafrostRole
    template_name = "permafrost/permafrostrole_users.html"
    permission_required = ["permafrost.view_permafrostrole"]
    permission_required_post = ["permafrost.add_user_to_role"]

    def get_queryset(self):
        return super().get_queryset().exclude(name__in=PERMAFROST_EXCLUDED_ROLES)

    def get_members(self):
        users = services.list_role_users(self.object)
        user_model = get_user_model()
        username_field = user_model.USERNAME_FIELD
        field_names = {field.name for field in user_model._meta.get_fields()}
        search = self.request.GET.get("q", "").strip()

        if search:
            search_query = Q(**{f"{username_field}__icontains": search})
            if "email" in field_names:
                search_query |= Q(email__icontains=search)
            users = users.filter(search_query)

        return users.order_by(username_field, "pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(
            self.get_members(), getattr(settings, "PERMAFROST_UI_PAGE_SIZE", 50)
        )
        page_obj = paginator.get_page(self.request.GET.get("page"))
        context.update(
            {
                "member_list": page_obj.object_list,
                "page_obj": page_obj,
                "paginator": paginator,
                "is_paginated": page_obj.has_other_pages(),
                "query": self.request.GET.get("q", "").strip(),
                "can_manage_members": has_all_permissions(
                    self.request, ["permafrost.add_user_to_role"]
                ),
            }
        )
        context.setdefault("add_form", RoleMembershipAddForm())
        context.setdefault("remove_form", RoleMembershipRemoveForm(role=self.object))
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get("action")
        add_form = RoleMembershipAddForm()
        remove_form = RoleMembershipRemoveForm(role=self.object)

        if action == "add":
            add_form = RoleMembershipAddForm(request.POST)
            if add_form.is_valid():
                users = add_form.users
                services.add_role_users(self.object, users)
                messages.success(
                    request,
                    ngettext(
                        "Added %(count)d user to this role.",
                        "Added %(count)d users to this role.",
                        len(users),
                    )
                    % {"count": len(users)},
                )
                return redirect("permafrost:role-users", slug=self.object.slug)
        elif action == "remove":
            remove_form = RoleMembershipRemoveForm(request.POST, role=self.object)
            if remove_form.is_valid():
                users = list(remove_form.cleaned_data["users"])
                services.remove_role_users(self.object, users)
                messages.success(
                    request,
                    ngettext(
                        "Removed %(count)d user from this role.",
                        "Removed %(count)d users from this role.",
                        len(users),
                    )
                    % {"count": len(users)},
                )
                return redirect("permafrost:role-users", slug=self.object.slug)
        else:
            add_form.add_error(None, _("Choose a membership action."))

        context = self.get_context_data(
            object=self.object,
            add_form=add_form,
            remove_form=remove_form,
        )
        return self.render_to_response(context)


class PermafrostRoleLookupView(PermafrostSiteMixin, TemplateView):
    template_name = "permafrost/permafrostrole_lookups.html"
    permission_required = ["permafrost.view_permafrostrole"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lookup_kind = self.request.GET.get("lookup")
        user_form = UserRoleLookupForm(
            self.request.GET if lookup_kind == "user" else None
        )
        permission_form = PermissionRoleLookupForm(
            self.request.GET if lookup_kind == "permission" else None
        )
        roles = None
        result_label = None

        if lookup_kind == "user" and user_form.is_valid():
            user = user_form.user
            roles = services.list_user_roles(user, request=self.request)
            result_label = _("Roles for %(user)s") % {"user": user.get_username()}
        elif lookup_kind == "permission" and permission_form.is_valid():
            permission = permission_form.cleaned_data["permission"]
            roles = services.list_permission_roles(permission, request=self.request)
            result_label = _("Roles granting %(permission)s") % {
                "permission": permission.name
            }

        context.update(
            {
                "lookup_kind": lookup_kind,
                "user_lookup_form": user_form,
                "permission_lookup_form": permission_form,
                "result_label": result_label,
                "lookup_submitted": lookup_kind in {"user", "permission"},
            }
        )

        lookup_query = self.request.GET.copy()
        lookup_query.pop("page", None)
        context["lookup_query"] = lookup_query.urlencode()

        if roles is not None:
            paginator = Paginator(
                roles.order_by("category", "name", "pk"),
                getattr(settings, "PERMAFROST_UI_PAGE_SIZE", 50),
            )
            page_obj = paginator.get_page(self.request.GET.get("page"))
            context.update(
                {
                    "role_list": page_obj.object_list,
                    "page_obj": page_obj,
                    "paginator": paginator,
                    "is_paginated": page_obj.has_other_pages(),
                }
            )

        return context
