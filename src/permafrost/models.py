import hashlib
import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db import models, transaction
from django.contrib.auth.models import Group, Permission

# from django.contrib.sites.shortcuts import get_current_site
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.contrib.sites.managers import CurrentSiteManager
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver
from django.urls import reverse
from .context import (
    DEFAULT_CONTEXT_MODEL,
    get_context_content_type,
    get_context_model_label,
    get_default_context_object,
)

logger = logging.getLogger(__name__)


###############
# CHOICES
###############

PERMAFROST_DEFAULT_ROLES = getattr(settings, "PERMAFROST_DEFAULT_ROLES", [])
PERMAFROST_EXCLUDED_ROLES = getattr(settings, "PERMAFROST_EXCLUDED_ROLES", [])
CATEGORIES = getattr(settings, "PERMAFROST_CATEGORIES", {})


###############
# UTILITIES
###############


def get_current_site(*args, **kwargs):
    return settings.SITE_ID


def get_permission_objects(natural_keys_list):
    permissions = []
    for item in natural_keys_list:
        if not isinstance(item, dict) or "permission" not in item:
            logger.warning(
                "Invalid permission entry in PERMAFROST_CATEGORIES: %r", item
            )
            continue
        try:
            permission = Permission.objects.get_by_natural_key(*item["permission"])
            permissions.append(permission)
        except (Permission.DoesNotExist, TypeError, ValueError):
            logger.warning(
                "Permission not found in PERMAFROST_CATEGORIES: %r",
                item["permission"],
            )

    return permissions


def get_required_by_category(category):
    category_data = CATEGORIES.get(category, {})
    if not isinstance(category_data, dict):
        return []
    return get_permission_objects(category_data.get("required", []))


def get_optional_by_category(category):
    category_data = CATEGORIES.get(category, {})
    if not isinstance(category_data, dict):
        return []
    return get_permission_objects(category_data.get("optional", []))


def get_all_perms_for_all_categories():
    perms = []
    for category, category_data in CATEGORIES.items():
        if not isinstance(category_data, dict):
            continue
        optional_perms = category_data.get("optional", [])
        required_perms = category_data.get("required", [])
        optional_and_required_perms = set(
            get_permission_objects(optional_perms)
            + get_permission_objects(required_perms)
        )
        perms.extend(optional_and_required_perms)

    return perms


###############
# MANAGERS
###############


class PermafrostRoleManager(models.Manager):
    """
    Standard Django manager with natural key support added.
    """

    def get_by_natural_key(
        self, slug, context_content_type_key=None, context_object_id=None
    ):
        if context_content_type_key is not None and context_object_id is not None:
            context_content_type = ContentType.objects.get_by_natural_key(
                *context_content_type_key
            )
            return self.get(
                slug=slug,
                context_content_type=context_content_type,
                context_object_id=context_object_id,
            )

        return self.get(slug=slug, site=context_content_type_key)


###############
# MIXINS
###############


###############
# MODELS
###############


def get_choices():
    """
    Creates a choice list based on the PERMAFROST_CATEGORIES settings.
    """
    return [
        (
            category_key,
            (
                category_data.get("label", category_key)
                if isinstance(category_data, dict)
                else category_key
            ),
        )
        for category_key, category_data in CATEGORIES.items()
    ]


def bounded_group_name(name):
    """Fit a generated role Group name within Django's configured limit."""
    max_length = Group._meta.get_field("name").max_length
    if len(name) <= max_length:
        return name

    digest = hashlib.sha256(name.encode("utf-8")).hexdigest()[:12]
    prefix_length = max_length - len(digest) - 1
    return f"{name[:prefix_length]}_{digest}"


class PermafrostRole(models.Model):
    """
    PermafrostRole is Client Defineable and "manages" a Django Group adding a
    user to this role adds them to the Django Group and automatically assignes
    them the permissions.

    The role is assigned to one of 3 categories to help group permission
    levels; 'administrator', 'staff' and 'user'.
    """

    name = models.CharField(_("Name"), max_length=50)
    slug = models.SlugField(_("Slug"))
    description = models.CharField(
        _("Description"), null=True, blank=True, max_length=200
    )
    category = models.CharField(
        _("Role Type"), max_length=32, choices=get_choices(), blank=False, null=False
    )  # These should stay fixed to not trigger a potenital migration issue with changing choices
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="permafrost_role",
        blank=True,
        null=True,
    )
    locked = models.BooleanField(
        _("Locked"), default=False
    )  # If this is locked, it can not be edited by the Client, used for System Default Roles
    deleted = models.BooleanField(
        _("Deleted"), default=False, help_text="Soft Delete the Role"
    )
    group = models.OneToOneField(
        Group,
        verbose_name=_("Group"),
        on_delete=models.CASCADE,
        related_name="permafrost_role",
        blank=True,
        null=True,
    )  # NOTE: Need to make sure this is exported with natural key values as it can have a different PK on different servers
    context_content_type = models.ForeignKey(
        ContentType,
        verbose_name=_("Context content type"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        editable=False,
    )
    context_object_id = models.PositiveBigIntegerField(
        _("Context object ID"), blank=True, null=True, editable=False
    )
    context = GenericForeignKey("context_content_type", "context_object_id")

    objects = PermafrostRoleManager()
    on_site = CurrentSiteManager()

    class Meta:
        verbose_name = _("Permafrost Role")
        verbose_name_plural = _("Permafrost Roles")
        constraints = [
            models.UniqueConstraint(
                fields=["name", "context_content_type", "context_object_id"],
                name="unique_permafrost_role_name_per_context",
            ),
            models.UniqueConstraint(
                fields=["slug", "context_content_type", "context_object_id"],
                name="unique_role_slug_per_context",
            ),
        ]

        permissions = (
            ("add_user_to_role", "Can Add Users to Role"),
            ("add_user_to_administration", "Can Add Users to the Administration Roles"),
        )

    def __str__(self):
        return self.name

    def natural_key(self):
        return (
            self.slug,
            self.context_content_type.natural_key(),
            self.context_object_id,
        )

    def get_absolute_url(self):
        return reverse("permafrost:role-detail", kwargs={"slug": self.slug})

    def get_update_url(self):
        return reverse("permafrost:role-update", kwargs={"slug": self.slug})

    # -------------
    # Permissions

    def required_permissions(self):
        """
        TODO: Read from the category and get the list of permissions
        """
        return get_required_by_category(self.category)

    def optional_permissions(self):
        """
        TODO!!!
        """
        return get_optional_by_category(self.category)

    def is_default_role(self):
        return self.name in PERMAFROST_DEFAULT_ROLES

    def all_perm_ids(self):
        req = [perm.pk for perm in self.required_permissions()]
        opt = [perm.pk for perm in self.optional_permissions()]
        return set(req + opt)

    def conform_group(self):
        """
        TODO!!!
        Based on the list of permissions in the Category, make sure the group
        has the right set.  Make sure no permissions are outside of the
        optional and required and that all required permissions are added.

        Make sure the Group has the required permissions and all others are
        within the Optional permissions.
        """
        self.permissions_set(
            self.group.permissions
        )  # This will check out to make sure all required permissions are present and optionals are allowed

    def get_group_name(self):
        """
        Creates the standard name for the group
        """
        context_object = self.get_context_object()
        if get_context_model_label() == DEFAULT_CONTEXT_MODEL and isinstance(
            context_object, Site
        ):
            return bounded_group_name(
                "{0}_{1}_{2}".format(context_object.pk, self.category, self.slug)
            )

        context_label = context_object._meta.label_lower.replace(".", "_")
        return bounded_group_name(
            "{0}_{1}_{2}_{3}".format(
                context_label,
                context_object.pk,
                self.category,
                self.slug,
            )
        )

    def validate_role_identity(self):
        if not self.slug:
            raise ValidationError(
                {"name": "Role name must contain characters that produce a URL slug."}
            )

        conflict = PermafrostRole.objects.filter(
            slug=self.slug,
            context_content_type=self.context_content_type,
            context_object_id=self.context_object_id,
        ).exclude(pk=self.pk)
        if conflict.exists():
            raise ValidationError(
                {"name": ("Role name conflicts with another role URL in this context.")}
            )

    def validate_group_name(self, group_name):
        if (
            self.group_id
            and PermafrostRole.objects.filter(group_id=self.group_id)
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError(
                {"group": "This Django Group already belongs to another role."}
            )

        conflict = Group.objects.filter(name=group_name)
        if self.group_id:
            conflict = conflict.exclude(pk=self.group_id)
        if conflict.exists():
            raise ValidationError(
                {
                    "name": (
                        "The generated Django Group name is already in use. "
                        "Choose another role name."
                    )
                }
            )

    def get_context_object(self):
        if self.context is not None:
            return self.context

        if self.site_id and get_context_model_label() == DEFAULT_CONTEXT_MODEL:
            return self.site

        return get_default_context_object()

    def set_context(self, context_object):
        self.context_content_type = get_context_content_type(context_object)
        self.context_object_id = context_object.pk
        self._state.fields_cache.pop("context", None)
        if isinstance(context_object, Site):
            self.site = context_object

    def permissions(self):
        return self.group.permissions

    def permissions_add(self, *args):
        """
        Add Django permission(s) to the attached group if the permission is in the allowed permissions
        """
        id_check = self.all_perm_ids()
        for perm in args:
            if perm.pk in id_check:
                self.group.permissions.add(perm)

    def permissions_remove(self, *args):
        """
        Remove Django permission(s) from the attached group if the permission is not in the list of required permissions
        """
        id_check = [required.pk for required in self.required_permissions()]
        for perm in args:
            if perm.pk not in id_check:
                self.group.permissions.remove(perm)

    def permissions_set(self, permissions):
        """
        This updates the group's Django permissions to only include what was passed in and passes the check against optional and required permissions.
        """
        id_check = [required.pk for required in self.optional_permissions()]
        submitted_permissions = (
            permissions.all() if hasattr(permissions, "all") else permissions
        )

        optional_perms = [
            perm for perm in submitted_permissions if perm.pk in id_check
        ]  # perms passed in that meet the optional filter check
        required_perms = self.required_permissions()

        # Set to values passed in that are in the optional list plus the required permissions.
        self.group.permissions.set(optional_perms + required_perms)

    def permissions_clear(self):  # TODO: Need to update
        """
        Remove all Django permissions from the group except the required.
        """
        if CATEGORIES[self.category][
            "required"
        ]:  # If there are any required permissions, set them
            self.group.permissions.set(self.required_permissions())
        else:  # Otherwise, clear it out completely
            self.group.permissions.clear()

    # -------------
    # Users

    def user_set(self):
        """
        Wrapper around the group that returns a queryset of all the user
        included in this role.
        """
        return self.group.user_set.all()

    def users_add(self, *users):
        """
        Pass in a User object to add to the PermafrostRole's Group
        """
        self.group.user_set.add(*users)

    def users_remove(self, *users):
        """
        Pass in a User object to remove from the PermafrostRole's Group
        """
        self.group.user_set.remove(*users)

    def users_clear(self):
        """
        Remove all users from the PermafrostRole's Group
        """
        self.group.user_set.clear()

    @transaction.atomic
    def ensure_group(self):
        """
        Ensure this role has the matching Django Group and that it is conformed
        to the role's allowed permissions.
        """
        group_name = self.get_group_name()
        self.validate_group_name(group_name)
        if not self.group_id:
            self.group = Group.objects.create(name=group_name)
            self.save(update_fields=["group"])
        elif self.group.name != group_name:
            self.group.name = group_name
            self.group.save()

        self.conform_group()
        return self.group

    # -------------
    # Save

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        if not self.context_content_type_id or not self.context_object_id:
            self.set_context(self.get_context_object())
        self.validate_role_identity()
        group_name = self.get_group_name()
        self.validate_group_name(group_name)

        if not self.pk:  # if this is a new role, create the matching group
            if not self.group_id:
                self.group = Group.objects.create(name=group_name)

        result = super().save(*args, **kwargs)

        if (
            self.group.name != group_name
        ):  # if the role is renamed after successful save, update the group's name
            self.group.name = group_name
            self.group.save()

        self.conform_group()  # Apply after a successful save and Group creation (if needed)

        return result

    # -------------
    # Delete

    @transaction.atomic
    def delete(self, using=None, keep_parents=False):
        if not self.locked and not self.is_default_role():
            return super().delete()


@receiver(
    post_delete,
    sender=PermafrostRole,
    dispatch_uid="delete_matching_permafrost_role_group",
)
def delete_matching_group(sender, instance, using, **kwargs):
    if (
        instance.group_id
        and not PermafrostRole.objects.using(using)
        .filter(group_id=instance.group_id)
        .exists()
    ):
        Group.objects.using(using).filter(pk=instance.group_id).delete()


@receiver(
    pre_delete,
    dispatch_uid="delete_permafrost_roles_for_context_object",
)
def delete_roles_for_context_object(sender, instance, using, **kwargs):
    if sender._meta.label_lower != get_context_model_label().lower():
        return

    context_content_type = ContentType.objects.db_manager(using).get_for_model(instance)
    PermafrostRole.objects.using(using).filter(
        context_content_type=context_content_type,
        context_object_id=instance.pk,
    ).delete()
