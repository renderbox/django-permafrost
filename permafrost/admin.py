from django.contrib import admin

from .models import PermafrostRole, PermafrostCategory

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

class PermafrostRoleAdmin(admin.ModelAdmin):
    readonly_fields = ('slug',)
    list_display = ('name', 'category')
    ordering = ('name',)
    readonly_fields=('group','slug')

    def get_readonly_fields(self, request, obj=None):
        if obj: # editing an existing object
            return self.readonly_fields + ('category',)
        return self.readonly_fields

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
