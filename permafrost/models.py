from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.contrib.auth.models import Group, Permission
from django.contrib.sites.shortcuts import get_current_site
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify


'''
A ROLE_CATEGORY defines what permissions are assignable per category
These are defined by developers and used by clients.
Only what is available here will be available to the Client to set.
For security reasons, this should be hard coded.

Example:

PERMAFROST_ROLE_CONFIG = {
    'User': {                   # Permission Grouping
        'permissions': [        # List of Django Permissions that are client configurable (as string or dict)
                {"perm":"permafrost.view_role", "label":"Can view Role"},
                {"perm":"permafrost.view_rolepermission", "label":"Can view Role Permission"},
            ],
        'choice': 1,             # The Value stored in the Choice Field
        'included': [           # Permissions the Group uses that are always included but not editable by the client
            '',
            ''
        ]
    },
    'Staff': {
        'permissions': [        # List of Django Permissions that are client configurable (as string or dict)
                {"perm":"permafrost.add_role", "label":"Can add Role"},
                {"perm":"permafrost.change_role", "label":"Can change Role"},
                {"perm":"permafrost.view_role", "label":"Can view Role"},
                {"perm":"permafrost.add_rolepermission", "label":"Can add Role Permission"},
                {"perm":"permafrost.change_rolepermission", "label":"Can change Role Permission"},
                {"perm":"permafrost.view_rolepermission", "label":"Can view Role Permission"},
            ],
        'choice': 30,            # The Value stored in the Choice Field
        'include: [
            "permafrost.view_role",
            "permafrost.view_rolepermission",
        ]
    },
    'Administrator': {
        'permissions': [        # List of Django Permissions that are client configurable (as string or dict)
                {"perm":"permafrost.add_role", "label":"Can add Role"},
                {"perm":"permafrost.change_role", "label":"Can change Role"},
                {"perm":"permafrost.delete_role", "label":"Can delete Role"},
                {"perm":"permafrost.view_role", "label":"Can view Role"},
                {"perm":"permafrost.add_rolepermission", "label":"Can add Role Permission"},
                {"perm":"permafrost.change_rolepermission", "label":"Can change Role Permission"},
                {"perm":"permafrost.delete_rolepermission", "label":"Can delete Role Permission"},
                {"perm":"permafrost.view_rolepermission", "label":"Can view Role Permission"},
            ],
        'choice': 50,
        'included': [
            '',
            ''
        ]
    }
}
'''

ROLE_CONFIG = getattr(settings, "PERMAFROST_ROLE_CONFIG")

###############
# CHOICES
###############

ROLE_CATEGORY_CHOICES = [(value['choice'], key) for key,value in ROLE_CONFIG.items()]      # Used to help manage permission presentation

###############
# UTILITIES
###############

def name_from_choice(choices, value):
    return [x[1] for x in choices if x[0] == value][0]

def value_as_list(value):
    '''
    Takes whatever is passed in and tries to return it as a list
    '''

    if isinstance(value, list):
        return value
    
    if value == None:
        return []

    return [value]


###############
# MODELS
###############

class Role(models.Model):
    '''
    Role is Client Defineable and "wraps" around a Django Group
    adding a user to this role adds them to the Django Group
    and automatically assignes them the permissions.
    '''
    name = models.CharField(_("Name"), max_length=50)
    slug = models.SlugField(_("Slug"))
    category = models.IntegerField(_("Role Category"), choices=ROLE_CATEGORY_CHOICES, default=1)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, default=settings.SITE_ID)
    group = models.OneToOneField(Group, verbose_name=_("Group"), on_delete=models.CASCADE, blank=True, null=True)      # Need to be uneditable in the Admin
    locked = models.BooleanField(_("Locked"), default=False)                                                   # If this is locked, it can not be edited by the Client, used for defaults

    class Meta:
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")
        unique_together = [['name', 'site']]

    def __str__(self):
        return self.name

    def get_permission_models(self, permissions=None):
        result = []
        choice = None

        permissions = value_as_list(permissions)

        for key, value in ROLE_CONFIG.items():
            if value['choice'] == self.category:
                choice = value
                break

        if choice != None:
            for permission in permissions:                  # Return all available permissions for now, TODO: move this to a query if possible to avoid all the DB hits
                if permission in choice['permissions']:     # Do a check to make sure it's available to the user catagory
                    result.append(permission_from_string(permission))

            # for include in choice['includes']
            # TODO: Add "included" permissions to make sure they are always there

        return result

    def permission_from_string(self, permission):
        values = permission.split(".")
        return Permission.objects.get(codename=values[1], content_type__app_label=values[0])

    #-------------
    # Permissions

    def permissions_add(self, permissions):
        '''
        Add permissions to the attached group by name "app.perm"
        '''
        for p in self.get_permission_models(permissions=permissions):
            self.group.permissions.add(p)

    def permissions_remove(self, permissions):
        '''
        Remove permissions from the attached group by name "app.perm"
        '''
        for p in self.get_permission_models(permissions=permissions):
            self.group.permissions.remove(p)

    def permissions_clear(self, includes=True):
        '''
        Remove all permissions from the attached group
        '''
        self.group.permissions.clear()

        # Add back includes
        if includes:
            choice = name_from_choice(self.category)
            includes = ROLE_CONFIG[choice]['includes']
            self.permissions_add(includes)

    #-------------
    # Users

    def users_add(self, users=None):
        '''
        Pass in a User object to add to the Role
        '''
        for user in value_as_list(users):
            user.groups.add(self.group)

    def users_remove(self, users=None):
        '''
        Pass in a User object to remove from the Role
        '''
        for user in value_as_list(users):
            user.groups.remove(self.group)

    def users_clear(self):
        '''
        Remove all users from the Role
        '''
        self.group.clear()

    #-------------
    # Save

    def save(self, *args, **kwargs):

        self.slug = slugify(self.name)

        if not self.group:
            category = name_from_choice(ROLE_CATEGORY_CHOICES, self.category)
            new_group, created = Group.objects.get_or_create( name="{0}_{1}_{2}".format( self.site.pk, slugify(category), slugify(self.name)) )
            if created:
                new_group.save()
            self.group = new_group

        return super().save(*args, **kwargs)
