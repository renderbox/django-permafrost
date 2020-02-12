from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from django.contrib.auth.models import User

from permafrost.api import PermafrostRESTPermission


class PermCheckAPIView(APIView):
    """
    """
    # authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [PermafrostRESTPermission]
    permission_required = ('permafrost.add_role',)

    def get(self, request, format=None):
        """
        Return a list of all users.
        """
        perm_list = list(request.user.get_all_permissions())
        perm_list.sort()
        return Response(perm_list)
