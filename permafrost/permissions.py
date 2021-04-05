"""
This is a permission class that will only work for Django Rest Framework.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
try:
    from rest_framework.permissions import BasePermission
except ImportError:
    # If django rest framework is not installed, make it a useless object
    BasePermission = object

#--------------
# DJANGO REST PERMS
#--------------

class PermafrostRESTPermission(BasePermission):

    def has_permission(self, request, view):
        perms = getattr(view, "permission_required", set() )
        method_perms = getattr(view, "permission_required_" + request.method.lower(), set() )

        check_list = list(perms) + list(method_perms)
        user_perms = list(request.user.get_all_permissions())

        # Get the user's perms and check that all the itms in the list are present
        for perm in check_list:
            if perm not in user_perms:
                return False

        return True

class PermafrostRESTSitePermission(BasePermission):
    
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        has_permission = False

        perms = getattr(view, "permission_required", set() )
        method_perms = getattr(view, "permission_required_" + request.method.lower(), set() )
        
        check_list = list(perms) + list(method_perms)
        
        if not check_list:
            return True
            
        user_groups_field = get_user_model()._meta.get_field('groups')
        user_groups_query = 'group__%s' % user_groups_field.related_query_name()
        
        user_permissions = Permission.objects.filter(
            **{user_groups_query: request.user}, 
            group__permafrost_role__site=request.site
        )

        for perm in check_list:
            try:
                app_label, codename = perm.split('.')
                qry = {}
                qry['content_type__app_label'] =  app_label
                if codename:
                    qry['codename'] = codename
                user_permissions.get(**qry)
                has_permission = True
            except Permission.DoesNotExist:
                return False
            
        return has_permission
