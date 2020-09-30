"""
This is a permission class that will only work for Django Rest Framework.
"""

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

