# import sys
from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.contrib.auth.models import Group, Permission

# from django.contrib.sites.shortcuts import get_current_site
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.sites.managers import CurrentSiteManager
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.urls import reverse

from jsonfield import JSONField  # Using this instead of the PSQL one for portability

import logging

logger = logging.getLogger(__name__)


###############
# CHOICES
###############


try:
    CATEGORIES = getattr(settings, "PERMAFROST_CATEGORIES")
except AttributeError:
    print(
        """
    !!! Warning: PERMAFROST_CATEGORIES are not defined!

    They should look something like this and be defined in settings.py

    PERMAFROST_CATEGORIES = {
        'administration': {
            'label': _('Administration'),
            'level': 50,
            'optional': [
                {'label': _('Can delete Role'), 'permission': ('delete_permafrostrole', 'permafrost', 'permafrostrole') },
            ],
            'required': [
                {'label': _('Can add Role'), 'permission': ('add_permafrostrole', 'permafrost', 'permafrostrole') },
                {'label': _('Can change Role'), 'permission': ('change_permafrostrole', 'permafrost', 'permafrostrole') },
                {'label': _('Can view Role'), 'permission': ('view_permafrostrole', 'permafrost', 'permafrostrole') },
            ],
        },
        'staff': {
            'label': _('Staff'),
            'level': 30,
            'optional': [
                {'label': _('Can add Role'), 'permission': ('add_permafrostrole', 'permafrost', 'permafrostrole') },
                {'label': _('Can change Role'), 'permission': ('change_permafrostrole', 'permafrost', 'permafrostrole') },
                {'label': _('Can view Role'), 'permission': ('view_permafrostrole', 'permafrost', 'permafrostrole') },
            ],
            'required': [
                {'label': _('Can view Role'), 'permission': ('view_permafrostrole', 'permafrost', 'permafrostrole') },
            ],
        },
        'user': {
            'label': _('User'),
            'level': 1,
            'optional': [
                {'label': _('Can view Role'), 'permission': ('view_permafrostrole', 'permafrost', 'permafrostrole') },
            ],
            'required': [],
        },
    }

    See README.md for more information.
    """
    )
    # sys.exit()
    raise


###############
# UTILITIES
###############


def get_current_site(*args, **kwargs):
    return settings.SITE_ID


def get_permission_objects(natural_keys_list):
    permissions = []
    for item in natural_keys_list:
        try:
            permission = Permission.objects.get_by_natural_key(*item["permission"])
            permissions.append(permission)
        except:
            logger.warn(
                f'Permission not found in PERMAFROST_CATEGORIES: {item["permission"]}'
            )
            pass

    return permissions


def get_required_by_category(category):
    if "required" in CATEGORIES[category]:
        return get_permission_objects(CATEGORIES[category]["required"])
    return []


def get_optional_by_category(category):
    if "optional" in CATEGORIES[category]:
        return get_permission_objects(CATEGORIES[category]["optional"])
    return []


###############
# MANAGERS
###############


class PermafrostRoleManager(models.Manager):
    """
    Standard Django manager with natural key support added.
    """

    def get_by_natural_key(self, slug, site):
        return self.get(slug=slug, site=site)


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
    return [(cat_key, CATEGORIES[cat_key]["label"]) for cat_key in CATEGORIES.keys()]


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
        default=get_current_site,
        related_name="permafrost_role",
    )  # This uses a callable so it will not trigger a migration with the projects it's included in
    locked = models.BooleanField(
        _("Locked"), default=False
    )  # If this is locked, it can not be edited by the Client, used for System Default Roles
    deleted = models.BooleanField(
        _("Deleted"), default=False, help_text="Soft Delete the Role"
    )
    group = models.ForeignKey(
        Group,
        verbose_name=_("Group"),
        on_delete=models.CASCADE,
        related_name="permafrost_role",
        blank=True,
        null=True,
    )  # NOTE: Need to make sure this is exported with natural key values as it can have a different PK on different servers

    objects = PermafrostRoleManager()
    on_site = CurrentSiteManager()

    class Meta:
        verbose_name = _("Permafrost Role")
        verbose_name_plural = _("Permafrost Roles")
        unique_together = (("name", "site"),)

        permissions = (
            ("add_user_to_role", "Can Add Users to Role"),
            ("add_user_to_administration", "Can Add Users to the Administration Roles"),
        )

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.slug, self.site)

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
        return "{0}_{1}_{2}".format(self.site.pk, self.category, self.slug)

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

        optional_perms = [
            perm for perm in permissions.all() if perm.pk in id_check
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

    # -------------
    # Save

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        group_name = self.get_group_name()

        if not self.pk:  # if this is a new role, create the matching group
            self.group, created = Group.objects.get_or_create(
                name=group_name
            )  # Add the group if one named correctly alreay exists, otherwise create a new one.

        result = super().save(*args, **kwargs)

        if (
            self.group.name != group_name
        ):  # if the role is renamed after successful save, update the group's name
            self.group.name = group_name
            self.group.save()

        self.conform_group()  # Apply after a successful save and Group creation (if needed)

        return result


@receiver(
    post_delete,
    sender=PermafrostRole,
    dispatch_uid="delete_matching_permafrost_role_group",
)
def delete_matching_group(sender, instance, using, **kwargs):
    instance.group.delete()
