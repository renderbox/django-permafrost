import json

from django.test import TestCase 
from django.contrib.sites.models import Site
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.db import transaction

from permafrost.models import Role, ROLE_CONFIG, get_permission_models

class RoleModelTest(TestCase):

    # fixtures = ['unit_test']

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='john', email='jlennon@beatles.com', password='Passw0rd!')
        self.staffuser = User.objects.create_user(username='staffy', email='staffy@beatles.com', password='Passw0rd!')
        self.adminuser = User.objects.create_user(username='adminy', email='adminy@beatles.com', password='Passw0rd!')

        self.site_1 = Site.objects.create(name="This Site", domain="thissite.com")
        self.site_2 = Site.objects.create(name="That Site", domain="thatsite.com")

    #     self.client_user = get_user_model().objects.get(pk=5)
    #     self.client_staff = get_user_model().objects.get(pk=6)
    #     self.client_admin = get_user_model().objects.get(pk=7)

    def test_permission_objects_from_string(self):
        perms = get_permission_models("permafrost.view_role")

        self.assertEqual(1, len(perms))

    def test_permission_objects_from_string_list(self):
        perms = get_permission_models( ["permafrost.view_role", "permafrost.change_role"] ) 

        self.assertEqual(2, len(perms))

    def test_create_user_role(self):
        # Test that creating a Role creates a matching Group

        role = Role(name="Bobs Super Group")
        role.save()

        self.assertEqual(role.group.name, "1_user_bobs-super-group")        # Checks that the user is created

        # Add the user to the Role with the 
        role.users_add(self.user)

        # perms = [x.name for x in role.group.permissions.all()]
        # Get the list from the user?
        perms = list(self.user.get_all_permissions())

        # Test that "included" permissions are always present in the group
        self.assertEqual(perms, [])

    # def test_role_permission_limits(self):
        # Test that creating a Role creates a matching Group

        # Test that permissions only in the Category's list can be added to the Role

            # Get a list of the current permissions

            # try to add a permission

            # Check to see if it was added

    def test_create_staffuser_role(self):
        # Test that creating a Role creates a matching Group

        role = Role(name="Bobs Staff Group", category=30)
        role.save()

        self.assertEqual(role.group.name, "1_staff_bobs-staff-group")        # Checks that the user is created

        # Add user to the Group
        role.users_add(self.staffuser)
        perms = list(self.staffuser.get_all_permissions())
        perms.sort()

        check_list = ["permafrost.view_role",  "permafrost.change_role"]    # Needs to be sorted to try to make sure it's a close to the same as possible
        check_list.sort()

        # Test that "included" permissions are the only things present in the group
        self.assertEqual(perms, check_list)

    def test_only_allowed_category_perms_can_be_added(self):
        # Test that permissions not in the Category's list can not be added to the Role
        pass

    def test_create_duplicate_role(self):
        # Test that creating a Role of the same name producers and error
        role_a = Role(name="Bobs Super Group", site=self.site_1)
        role_a.save()

        role_c = Role(name="Bobs Super Group", site=self.site_2)
        role_c.save()

        with self.assertRaises(IntegrityError):

            with transaction.atomic():
                role_b = Role(name="Bobs Super Group", site=self.site_2)
                role_b.save()

            with transaction.atomic():
                role_d = Role(name="Bobs Super Group", site=self.site_2, category=30)
                role_d.save()

        # TODO: Add check to make sure Role's Groups were not created

    def test_clear_role_permissions(self):
        # Test that "included" permissions are always present in the group

        role = Role(name="Bobs Staff Group", site=self.site_2, category=30)

    #     Add Extra Permissions from the list
    #     Clear
    #     Make sure only the includes are present
    #     raise NotImplementedError

    # Test the Client Users permissions

    # def test_django_admin_has_all_permissions(self):
    #     # Test the Django Users permissions
    #     raise NotImplementedError

    # Test that deleting a Role deletes the matching group


#     def test_superuser_has_perms(self):
#         '''
#         Test that a user with
#         '''
#         View = self.get_view("any", ['edit-step', 'edit-path'])
#         request = self.get_request('/', self.superuser)

#         response = View.as_view()(request)
#         self.assertEqual(response.status_code, 200)
