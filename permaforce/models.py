from django.db import models

from django.utils.translation import ugettext_lazy as _
# from autoslug import AutoSlugField

# PERMISSION_CATEGORY_CHOICES = (('user','User'), ('staff','Staff'), ('administrator','Administrator')) # Used to help manage permission presentation


# #--------------
# # MIXIN MODELS
# #--------------

# class UserPermMixin(object):

#     def perms(self):
#         result = set()

#         for role in self.roles.all():           # todo: move this to a query if possible
#             for p in role.perms.all(): 
#                 result.add(p.slug)
                
#         return result                           # Returns a set for easier comparisons

#     def perm_check(self, perms=[], mode="any"):
#         '''
#         In a view with a the Perm Check Mixin added, check to see if 
#         the perms are in the compiled list of this user's perms.

#         Perms are in the 'slug' form for the permission object.

#         modes:
#             any -> If there are any matches
#             all -> If all perms are present
#         '''
#         return True


# #--------------
# # MODELS
# #--------------

# class Perm(models.Model):
#     '''
#     These are a list of permissions (perms) that get checked per view.
#     Perms are not site defined so they are not editable by Site Administrators.
#     '''
#     name = models.CharField(_("Name"), max_length=100, blank=False)
#     slug = AutoSlugField(populate_from='name')
#     enabled = models.BooleanField(_("Enabled"), default=True)      # This is used to keep things from breaking after 'collecting perms' from views
#     category = models.CharField(_("Perm Category"), max_length=20, blank=False, choices=PERMISSION_CATEGORY_CHOICES, default=PERMISSION_CATEGORY_CHOICES[0][0])   # This is used for secondary level checking

#     def __str__(self):
#         return self.name
