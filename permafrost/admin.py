from pprint import pprint
import json

from django.contrib import admin
from django.shortcuts import render

from .models import PermafrostRole, PermafrostCategory

################
# ADMIN ACTIONS
################


def perms_to_code(modeladmin, request, queryset):

    result = {}

    for role in queryset.all():

        key = role.category.name.lower()

        if not key in result:       # First time though, assume everything available is required
            result[key] = {'req':list(role.group.permissions.all()), 'opt':[], 'label':role.category.name, 'access_level':role.category.level}
        else:
            new_perms = list(role.group.permissions.all())

            for perm in new_perms:
                if perm.pk not in [p.pk for p in result[key]['req']]:      # If the perm not shared with the previous, make it optional
                    result[key]['opt'].append(perm)

            new_req = []                            # Check previous required against the current
            for perm in result[key]['req']:
                if perm not in new_perms:               # If it's not shared, it's optional
                    result[key]['opt'].append(perm)
                else:                               # if it is shared, it's required
                    new_req.append(perm)

            result[key]['req'] = new_req

    pprint(result, indent=4)

    ordered = list(result.keys())
    ordered.sort()

    for key in ordered:
        result[key]['optional'] = [{'label':perm.name, 'permission':perm.natural_key()} for perm in result[key].pop('opt')]
        result[key]['required'] = [{'label':perm.name, 'permission':perm.natural_key()} for perm in result[key].pop('req')]

    return render(request, 'permafrost/admin/perms_to_code.html', context={'json_data':"PERMAFROST_CATEGORIES = {}".format(json.dumps(result, indent=4))})


perms_to_code.short_description = "Convert Model Permissions to Code"


def create_missing_groups(modeladmin, request, queryset):

    for item in queryset.all():
        # Make sure group exists and create if not after model is saved.
        item.get_group()


create_missing_groups.short_description = "Create a Django Group if missing"


###############
# MODEL ADMINS
###############

class PermafrostRoleAdmin(admin.ModelAdmin):
    readonly_fields = ('slug',)
    list_display = ('name', 'category', 'group', 'site')
    ordering = ('name',)
    readonly_fields=('slug',)
    actions = [create_missing_groups, perms_to_code]


class PermafrostCategoryAdmin(admin.ModelAdmin):
    readonly_fields = ('slug',)
    list_display = ('name',)
    ordering = ('name',)
    readonly_fields=('slug',)

###############
# REGISTRATION
###############

admin.site.register(PermafrostRole, PermafrostRoleAdmin)
admin.site.register(PermafrostCategory, PermafrostCategoryAdmin)
