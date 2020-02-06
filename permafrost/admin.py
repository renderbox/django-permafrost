from django.contrib import admin

from .models import Role

# ################
# # ADMIN ACTIONS
# ################

# def recreate_slug(modeladmin, request, queryset):
#     '''
#     This uses the save() instead of update() since the AutoSlugField is only generated on save().
#     '''
#     for item in queryset.all():
#         item.slug = ""
#         item.save()

# recreate_slug.short_description = "Regenerate the Slug Field"


# def make_enabled(modeladmin, request, queryset):
#     queryset.update(enabled=True)

# make_enabled.short_description = "Mark Enabled"


# def make_disabled(modeladmin, request, queryset):
#     queryset.update(enabled=False)

# make_disabled.short_description = "Mark Disabled"


###############
# MODEL ADMINS
###############

class RoleAdmin(admin.ModelAdmin):
    # readonly_fields = ('slug',)
    # list_display = ('name', 'category')
    # ordering = ('name',)
    readonly_fields=('group','slug')


# class RolePermissionAdmin(admin.ModelAdmin):
#     # readonly_fields = ('slug',)
#     # list_display = ('name', 'category')
#     # ordering = ('name',)
#     pass


###############
# REGISTRATION
###############

admin.site.register(Role, RoleAdmin)
# admin.site.register(RolePermission, RolePermissionAdmin)
