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
    list_display = ('name', 'category', 'role_group')
    ordering = ('name',)
    readonly_fields=('slug',)
    actions = [create_missing_groups]

    def get_readonly_fields(self, request, obj=None):
        if obj: # editing an existing object
            return self.readonly_fields + ('category',)
        return self.readonly_fields

    def role_group(self, obj):
        return obj.get_group().name


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
