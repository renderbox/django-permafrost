from django.contrib import admin

# from .models import Perm

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


# ###############
# # MODEL ADMINS
# ###############

# class PermAdmin(admin.ModelAdmin):
#     readonly_fields = ('slug',)
#     list_display = ('name', 'slug', 'enabled')
#     ordering = ('name',)
#     actions = [recreate_slug, make_enabled, make_disabled]
#     list_per_page = 25


# ###############
# # REGISTRATION
# ###############

# admin.site.register(Perm, PermAdmin)
