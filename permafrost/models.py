from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.contrib.auth.models import Group, Permission
from django.contrib.sites.shortcuts import get_current_site
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify

from autoslug import AutoSlugField

###############
# CHOICES
###############

ROLE_CATEGORY_CHOICES = ((1,'User'), (30,'Staff'), (50,'Administrator')) # Used to help manage permission presentation


###############
# SETTINGS
###############

# CURRENT_SITE = Site.objects.get_current()


###############
# MODELS
###############

class RolePermission(models.Model):
    '''
    A RolePermission defines what permissions are assignable per category
    These are defined by the site administrators and used by clients.
    Only what is connected will be seen by the Client.
    '''
    name = models.CharField(_("Name"), max_length=50, blank=True, null=True)       # Done this way for admin interface, display and to geenrate slugs.  
    slug = AutoSlugField(populate_from='name')
    category = models.IntegerField(_("Role Category Level"), choices=ROLE_CATEGORY_CHOICES, default=1)
    settings = models.TextField(_("Settings"), blank=True, null=True)
    permission = models.OneToOneField(Permission, verbose_name=_("Django Permission"), on_delete=models.CASCADE) # Permissions that are available to that category

    class Meta:
        verbose_name = _("Role Permission")
        verbose_name_plural = _("Role Permissions")
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("permafrost-role-permission-detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.permission.name
        return super().save(*args, **kwargs)


class Role(models.Model):
    '''
    Role is Client Defineable and "wraps" around a Django Group
    adding a user to this role adds them to the Django Group
    and automatically assignes them the permissions.
    '''
    name = models.CharField(_("Name"), max_length=50)
    slug = AutoSlugField(populate_from='name')
    category = models.IntegerField(_("Role Category"), choices=ROLE_CATEGORY_CHOICES, default=1)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, default=settings.SITE_ID)
    settings = models.TextField(_("Settings"), blank=True, null=True)
    role_permissions = models.ManyToManyField(RolePermission, verbose_name=_("Role Permissions"), related_name="roles")
    group = models.OneToOneField(Group, verbose_name=_("Groups"), on_delete=models.CASCADE)     # Need to be uneditable in the Admin
    locked = models.BooleanField(_("Locked"))

    class Meta:
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("permafrost-role-detail", kwargs={"slug": self.slug})

    def get_permissions(self):
        return [x.permission for x in self.role_permissions.objects.all()]

    def save(self, *args, **kwargs):

        # Create the Group
        if not self.group:
            self.group = Group(name="{0}_{}".format( settings.SITE_ID, slugify(self.name) ))

        permissions = self.get_permissions()

        # remove what's not needed

        # Add ther perms to it
        for p in permissions:
            self.group.permissions.add(p)

        return super().save(*args, **kwargs)
