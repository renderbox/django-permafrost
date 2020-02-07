import json

from django.test import TestCase 
from django.contrib.sites.models import Site
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

from permafrost.models import Role, ROLE_CONFIG

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

        # Test that permissions not in the Category's list can not be added to the Role

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

        # Check if user has the proper permissions
        # Test that "included" permissions are always present in the group
        self.assertEqual(perms, ["permafrost.view_role",  "permafrost.view_rolepermission"])

        # Test that permissions not in the Category's list can not be added to the Role


    def test_create_duplicate_role(self):
        # Test that creating a Role of the same name producers and error
        role_a = Role(name="Bobs Super Group", site=self.site_1)
        role_a.save()

        role_c = Role(name="Bobs Super Group", site=self.site_2)
        role_c.save()

        with self.assertRaises(IntegrityError):
            role_b = Role(name="Bobs Super Group", site=self.site_2)
            role_b.save()


    def test_clear_role_permissions(self):
        # Test that "included" permissions are always present in the group
        raise NotImplementedError

    # Test the Client Users permissions

    # Test the Django Users permissions

    # Test that deleting a Role deletes the matching group



#     def test_superuser_has_perms(self):
#         '''
#         Test that a user with
#         '''
#         View = self.get_view("any", ['edit-step', 'edit-path'])
#         request = self.get_request('/', self.superuser)

#         response = View.as_view()(request)
#         self.assertEqual(response.status_code, 200)
