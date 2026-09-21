# Permafrost Forms
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.forms import Form, ModelForm
from django.forms.fields import BooleanField, CharField, ChoiceField
from django.forms.models import ModelMultipleChoiceField
from django.forms.widgets import CheckboxInput, CheckboxSelectMultiple, Textarea
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .api import services
from .context import get_default_context_object
from .models import PermafrostRole, get_choices, get_optional_by_category

CHOICES = [("", _("Choose Role Type"))] + get_choices()

LABELS = {"name": _("Role Name"), "category": _("Role Type")}


def assemble_optiongroups_for_widget(permissions):
    choices = []
    optgroups = {}
    if permissions:
        for perm in permissions:
            if perm.content_type.name in optgroups:
                optgroups[perm.content_type.name].append(
                    (
                        perm.pk,
                        perm.name,
                    )
                )
            else:
                optgroups[perm.content_type.name] = [
                    (
                        perm.pk,
                        perm.name,
                    )
                ]

    for model_name, options in optgroups.items():
        choices.append([model_name, options])

    return choices


def bootstrappify(fields):
    for field in fields:
        widget = fields[field].widget
        if not isinstance(widget, CheckboxInput):
            if "class" in widget.attrs:
                widget.attrs["class"] = widget.attrs["class"] + " form-control"
            else:
                widget.attrs.update({"class": "form-control"})


class SelectPermafrostRoleTypeForm(ModelForm):
    name = CharField(required=False)
    description = CharField(required=False)
    category = ChoiceField(choices=CHOICES)

    class Meta:
        model = PermafrostRole
        fields = (
            "name",
            "description",
            "category",
        )
        labels = LABELS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bootstrappify(self.fields)


class PermafrostRoleCreateForm(ModelForm):
    permissions = ModelMultipleChoiceField(
        queryset=Permission.objects.all(), required=False
    )

    class Meta:
        model = PermafrostRole
        fields = ("name", "description", "category", "permissions")
        labels = LABELS

    def __init__(self, *args, **kwargs):
        self.context_object = kwargs.pop("context_object", None)
        self.site = kwargs.pop("site", None)
        if self.context_object is None:
            self.context_object = self.site or get_default_context_object()
        if self.site is None and isinstance(self.context_object, Site):
            self.site = self.context_object
        super().__init__(*args, **kwargs)
        self.instance.set_context(self.context_object)
        self.fields["category"].choices = CHOICES

        category = self.initial.get("category", self.data.get("category", None))

        if self.instance:
            category = self.instance.category if self.instance.category else category

        if category:
            all_optional_permissions = get_optional_by_category(category=category)
            ids = [perm.pk for perm in all_optional_permissions]

            self.fields["permissions"].queryset = Permission.objects.filter(id__in=ids)

        bootstrappify(self.fields)

    def save(self, commit=True):
        self.instance.set_context(self.context_object)
        instance = super().save(commit)
        category = instance.category

        if "permissions" in self.cleaned_data:
            perm_ids = []
            if category:
                perm_ids = self.cleaned_data["permissions"]
            if perm_ids:
                instance.permissions_set(Permission.objects.filter(id__in=perm_ids))
            else:
                instance.permissions_clear()
        return instance

    def clean_name(self):
        name = self.cleaned_data["name"]
        role_slug = slugify(name)
        if not role_slug:
            raise ValidationError(
                "Role name must contain characters that produce a URL slug."
            )

        conflict = PermafrostRole.objects.filter(
            slug=role_slug,
            context_content_type=self.instance.context_content_type,
            context_object_id=self.instance.context_object_id,
        ).exclude(pk=self.instance.pk)
        if conflict.exists():
            raise ValidationError(
                "Role name conflicts with another role URL in this context."
            )

        # Always return field
        return name


class PermafrostRoleUpdateForm(PermafrostRoleCreateForm):
    """
    Form used to display role detail
    Only allowed to edit optional permissions, name and description
    Category and required permissions stay locked
    """

    deleted = BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["category"].widget.attrs.update(
            {"readonly": True, "disabled": True}
        )
        self.fields["category"].disabled = True
        self.fields["category"].required = False
        self.fields["category"].choices = [
            choice for choice in CHOICES if choice[0] == self.instance.category
        ]
        self.fields["category"].initial = self.instance.category
        ## limit choices to saved category
        self.fields["deleted"].initial = self.instance.deleted

    def save(self, commit=True):
        if (
            self.cleaned_data["deleted"]
            and not self.instance.locked
            and not self.instance.is_default_role()
        ):
            self.instance.deleted = self.cleaned_data["deleted"]
        instance = super().save(commit)
        return instance


class RoleMembershipAddForm(Form):
    identifiers = CharField(
        label=_("User IDs"),
        help_text=_("Enter one value per line or separate values with commas."),
        widget=Textarea(attrs={"class": "form-control", "rows": 3}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lookup_field_name = getattr(
            settings, "PERMAFROST_API_USER_LOOKUP_FIELD", None
        )
        if self.lookup_field_name:
            lookup_field = services.get_user_lookup_field()
            self.fields["identifiers"].label = _("User %(field)s values") % {
                "field": lookup_field.verbose_name
            }

    def clean_identifiers(self):
        raw_value = self.cleaned_data["identifiers"]
        identifiers = list(
            dict.fromkeys(
                value.strip()
                for value in re.split(r"[,\r\n]+", raw_value)
                if value.strip()
            )
        )
        if not identifiers:
            raise ValidationError(_("Enter at least one user identifier."))

        try:
            if self.lookup_field_name:
                users = services.get_users_from_identifiers(identifiers)
            else:
                try:
                    user_ids = [int(identifier) for identifier in identifiers]
                except ValueError as exc:
                    raise ValidationError(_("Enter numeric user IDs.")) from exc
                users = services.get_users_from_ids(user_ids)
        except ValidationError as exc:
            raise ValidationError(exc.messages) from exc

        self.users = list(users)
        return identifiers


class RoleMembershipRemoveForm(Form):
    users = ModelMultipleChoiceField(
        queryset=get_user_model().objects.none(),
        required=True,
        widget=CheckboxSelectMultiple,
        error_messages={"required": _("Select at least one role member.")},
    )

    def __init__(self, *args, role, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["users"].queryset = services.list_role_users(role)
