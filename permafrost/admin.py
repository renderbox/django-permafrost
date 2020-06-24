from django.contrib import admin
from django.shortcuts import render

from .models import PermafrostRole, PermafrostCategory

################
# ADMIN ACTIONS
################


def perms_to_code(modeladmin, request, queryset):


    # Based on the selected Roles, what are the permissions in code format?

    


    return render(request, 'permafrost/admin/perms_to_code.html', context={'json_data':"BOBS STUFF\nHere"})


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
