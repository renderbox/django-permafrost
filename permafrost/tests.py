import json

from django.test import TestCase 
from django.contrib.sites.models import Site
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.db import transaction

from rest_framework.test import APIClient

from permafrost.models import PermafrostRole, PermafrostCategory, get_permission_models

class PermafrostRoleModelTest(TestCase):

    fixtures = ['unit_test']

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='john', email='jlennon@beatles.com', password='Passw0rd!')
        self.staffuser = User.objects.create_user(username='staffy', email='staffy@beatles.com', password='Passw0rd!')
        self.adminuser = User.objects.create_user(username='adminy', email='adminy@beatles.com', password='Passw0rd!')

        self.site_1 = Site.objects.get(pk=1)
        self.site_2 = Site.objects.get(pk=2)

        self.role_category_1 = PermafrostCategory.objects.get(pk=1)
        self.role_category_2 = PermafrostCategory.objects.get(pk=2)
        self.role_category_3 = PermafrostCategory.objects.get(pk=3)

    #     self.client_user = get_user_model().objects.get(pk=5)
    #     self.client_staff = get_user_model().objects.get(pk=6)
    #     self.client_admin = get_user_model().objects.get(pk=7)

    def test_permission_objects_from_string(self):
        perms = get_permission_models("permafrost.view_permafrostrole")

        self.assertEqual(1, len(perms))

    def test_permission_objects_from_string_list(self):
        perms = get_permission_models( ["permafrost.view_permafrostrole", "permafrost.change_permafrostrole"] ) 

        self.assertEqual(2, len(perms))

    def test_create_user_role(self):
        # Test that creating a PermafrostRole creates a matching Group

        role = PermafrostRole(name="Bobs Super Group", category=self.role_category_1)
        role.save()

        self.assertEqual(role.group.name, "1_user_bobs-super-group")        # Checks that the user is created

        # Add the user to the PermafrostRole with the 
        role.users_add(self.user)

        # perms = [x.name for x in role.group.permissions.all()]
        # Get the list from the user?
        perms = list(self.user.get_all_permissions())

        # Test that "included" permissions are always present in the group
        self.assertEqual(perms, [])

    # def test_role_permission_limits(self):
        # Test that creating a PermafrostRole creates a matching Group

        # Test that permissions only in the Category's list can be added to the PermafrostRole

            # Get a list of the current permissions

            # try to add a permission

            # Check to see if it was added

    def test_create_staffuser_role(self):
        # Test that creating a PermafrostRole creates a matching Group

        role = PermafrostRole(name="Bobs Staff Group", category=self.role_category_2)
        role.save()

        self.assertEqual(role.group.name, "1_staff_bobs-staff-group")        # Checks that the user is created

        # Add user to the Group
        role.users_add(self.staffuser)
        perms = list(self.staffuser.get_all_permissions())
        perms.sort()

        check_list = ["permafrost.view_permafrostrole"]    # Needs to be sorted to try to make sure it's a close to the same as possible
        check_list.sort()

        # Test that "included" permissions are the only things present in the group
        self.assertEqual(perms, check_list)

    def test_only_allowed_category_perms_can_be_added(self):
        # Test that permissions not in the Category's list can not be added to the PermafrostRole
        pass

    def test_create_duplicate_role(self):
        # Test that creating a PermafrostRole of the same name producers and error
        role_a = PermafrostRole(name="Bobs Super Group", site=self.site_1, category=self.role_category_1)
        role_a.save()

        role_c = PermafrostRole(name="Bobs Super Group", site=self.site_2, category=self.role_category_1)
        role_c.save()

        with self.assertRaises(IntegrityError):

            with transaction.atomic():
                role_b = PermafrostRole(name="Bobs Super Group", site=self.site_2, category=self.role_category_1)
                role_b.save()

            with transaction.atomic():
                role_d = PermafrostRole(name="Bobs Super Group", site=self.site_2, category=self.role_category_2)
                role_d.save()

        # TODO: Add check to make sure PermafrostRole's Groups were not created

    def test_clear_role_permissions(self):
        # Test that "included" permissions are always present in the group

        role = PermafrostRole(name="Bobs Staff Group", site=self.site_2, category=self.role_category_2)
        role.save()

        # print(len(role.permissions()))

        # self.assertEqual()

    #     Add Extra Permissions from the list
    #     run Clear method on role
    #     Make sure only the includes are present

    # Test the Client Users permissions

    # def test_django_admin_has_all_permissions(self):
    #     # Test the Django Users permissions
    #     raise NotImplementedError

    # Test that deleting a PermafrostRole deletes the matching group


#     def test_superuser_has_perms(self):
#         '''
#         Test that a user with
#         '''
#         View = self.get_view("any", ['edit-step', 'edit-path'])
#         request = self.get_request('/', self.superuser)

#         response = View.as_view()(request)
#         self.assertEqual(response.status_code, 200)


class PermafrostAPITest(TestCase):

    fixtures = ['unit_test']

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='john', email='jlennon@beatles.com', password='Passw0rd!')
        self.staffuser = User.objects.create_user(username='staffy', email='staffy@beatles.com', password='Passw0rd!', is_active=True, is_staff=True, )
        self.adminuser = User.objects.create_user(username='adminy', email='adminy@beatles.com', password='Passw0rd!', is_active=True, is_staff=True, is_superuser=True)

        self.site_1 = Site.objects.get(pk=1)
        self.site_2 = Site.objects.get(pk=2)

        self.role_category_1 = PermafrostCategory.objects.get(pk=1)
        self.role_category_2 = PermafrostCategory.objects.get(pk=2)
        self.role_category_3 = PermafrostCategory.objects.get(pk=3)

        self.client = APIClient()

    def test_superuser_can_access_permissions_endpoint(self):
        '''
        Uses a user that has all the permissions.
        '''
        self.client.force_authenticate(user=self.adminuser)
        response = self.client.get('/permissions/', format='json')
        assert response.status_code == 200

    def test_can_not_access_permissions_endpoint(self):
        '''
        Uses a user that does not have the required permission
        '''
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/permissions/', format='json')
        assert response.status_code == 403
