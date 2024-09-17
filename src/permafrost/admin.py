from pprint import pprint
import json

from django.contrib import admin
from django.shortcuts import render

from .models import PermafrostRole#, PermafrostCategory

################
# ADMIN ACTIONS
################


def perms_to_code(modeladmin, request, queryset):

    data = {}

    for role in queryset.all():
        
        if hasattr(role.category, 'name'):
            key = role.category.name.lower()
            label = role.category.name
        else:
            key = role.category
            label = role.get_category_display()
    
        if not key in data:       # First time though, assume everything available is required
            data[key] = {'req':list(role.group.permissions.all()), 'opt':[], 'label':label}
        else:
            new_perms = list(role.group.permissions.all())

            for perm in new_perms:
                if perm.pk not in [p.pk for p in data[key]['req']]:      # If the perm not shared with the previous, make it optional
                    data[key]['opt'].append(perm)

            new_req = []                            # Check previous required against the current
            for perm in data[key]['req']:
                if perm not in new_perms:               # If it's not shared, it's optional
                    data[key]['opt'].append(perm)
                else:                               # if it is shared, it's required
                    new_req.append(perm)

            data[key]['req'] = new_req

    # pprint(data, indent=4)

    key_order = list(data.keys())
    key_order.sort()

    result = ["from django.utils.translation import gettext_lazy as _\n", "PERMAFROST_CATEGORIES = {"]

    for key in key_order:
        result.append("    '{}': {{".format(key))
        result.append("        'label': _('{}'),".format(data[key]['label']))
        
        if data[key]['opt']:
            result.append("        'optional': [")
            for perm in data[key]['opt']:
                result.append("            {{'label': _('{}'), 'permission': {} }},".format(perm.name, perm.natural_key()) )
            result.append("        ],")
        else:
            result.append("        'optional': [],")

        if data[key]['req']:
            result.append("        'required': [")
            for perm in data[key]['req']:
                result.append("            {{'label': _('{}'), 'permission': {} }},".format(perm.name, perm.natural_key()) )
            result.append("        ],")
        else:
            result.append("        'required': [],")

        result.append("    },")
    result.append("}\n")


        # data[key]['optional'] = [{'label':perm.name, 'permission':perm.natural_key()} for perm in data[key].pop('opt')]
        # data[key]['required'] = [{'label':perm.name, 'permission':perm.natural_key()} for perm in data[key].pop('req')]

    return render(request, 'permafrost/admin/perms_to_code.html', context={'data':"\n".join(result)})
    # return render(request, 'permafrost/admin/perms_to_code.html', context={'json_data':"PERMAFROST_CATEGORIES = {}".format(json.dumps(data, indent=4))})


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


# class PermafrostCategoryAdmin(admin.ModelAdmin):
#     readonly_fields = ('slug',)
#     list_display = ('name',)
#     ordering = ('name',)
#     readonly_fields=('slug',)

###############
# REGISTRATION
###############

admin.site.register(PermafrostRole, PermafrostRoleAdmin)
# admin.site.register(PermafrostCategory, PermafrostCategoryAdmin)
