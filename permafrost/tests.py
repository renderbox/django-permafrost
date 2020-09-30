import json

from unittest import skipIf

from django.test import TestCase
from django.contrib.sites.models import Site
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.db import transaction
from django.contrib.auth.models import Group, Permission

try:
    from rest_framework.test import APIClient
    SKIP_DRF_TESTS = False
except ImportError:
    SKIP_DRF_TESTS = True

from permafrost.models import PermafrostRole


class PermafrostRoleModelTest(TestCase):

    fixtures = ['unit_test']

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='john', email='jlennon@beatles.com', password='Passw0rd!')
        self.staffuser = User.objects.create_user(username='staffy', email='staffy@beatles.com', password='Passw0rd!')
        self.administrationuser = User.objects.create_user(username='adminy', email='adminy@beatles.com', password='Passw0rd!')

        self.site_1 = Site.objects.get(pk=1)
        self.site_2 = Site.objects.get(pk=2)

        self.perm_view_permafrostrole = Permission.objects.get_by_natural_key(*('view_permafrostrole', 'permafrost', 'permafrostrole')) 
        self.perm_change_permafrostrole = Permission.objects.get_by_natural_key(*('change_permafrostrole', 'permafrost', 'permafrostrole')) 
        self.perm_delete_permafrostrole = Permission.objects.get_by_natural_key(*('delete_permafrostrole', 'permafrost', 'permafrostrole')) 
        self.perm_add_logentry = Permission.objects.get_by_natural_key(*('add_logentry', 'admin', 'logentry')) 

    def test_role_rename_updates_group(self):
        '''
        Make sure renaming the PermafrostRole properly renames the Django Group model.
        '''
        role = PermafrostRole(name="Awesome Students", category="user")
        role.save()

        pk_check = role.group.pk
        self.assertEqual(role.group.name, "1_user_awesome-students")

        role.name = "OK Students"
        role.save()

        new_role_group = Group.objects.get(name=role.get_group_name())

        self.assertEqual(role.group.name, "1_user_ok-students")
        self.assertEqual(role.group.pk, pk_check)                   # Make sure a new group was not generated
        
    # User Roles

    def test_create_user_role(self):
        '''
        Test that creating a PermafrostRole creates a matching Group
        '''
        role = PermafrostRole(name="Bobs Super Group", category="user")
        role.save()
        role.users_add(self.user)
        perms = list(self.user.get_all_permissions())

        self.assertEqual(list(role.group.permissions.all()), [])            # Check the permissions on the group
        self.assertEqual(role.group.name, "1_user_bobs-super-group")        # Checks that the user is created
        self.assertEqual(perms, [])

    def test_add_optional_to_user_role(self):
        '''
        Test that the optional role can be added
        '''
        role = PermafrostRole(name="Bobs Super Group", category="user")
        role.save()
        role.permissions_add(self.perm_view_permafrostrole)
        role.users_add(self.user)
        perms = list(self.user.get_all_permissions())

        self.assertListEqual(list(role.group.permissions.all()), [self.perm_view_permafrostrole])            # Check the permissions on the group
        self.assertEqual(role.group.name, "1_user_bobs-super-group")        # Checks that the user is created
        self.assertListEqual(perms, ["permafrost.view_permafrostrole"])

    def test_add_not_allowed_to_user_role(self):
        '''
        Test that a permission that is not optional or required can be added
        '''
        role = PermafrostRole(name="Bobs Super Group", category="user")
        role.save()
        role.permissions_add(self.perm_delete_permafrostrole)
        role.users_add(self.user)
        perms = list(self.user.get_all_permissions())

        self.assertEqual(list(role.group.permissions.all()), [])            # Check the permissions on the group
        self.assertEqual(role.group.name, "1_user_bobs-super-group")        # Checks that the user is created
        self.assertListEqual(perms, [])

    def test_clear_permissions_on_user_role(self):
        '''
        Test that clearning permissions restores them to just the required.
        '''
        role = PermafrostRole(name="Bobs Super Group", category="user")
        role.save()
        role.permissions_add(self.perm_view_permafrostrole)
        role.permissions_clear()
        role.users_add(self.user)
        perms = list(self.user.get_all_permissions())

        self.assertEqual(list(role.group.permissions.all()), [])            # Check the permissions on the group
        self.assertEqual(role.group.name, "1_user_bobs-super-group")        # Checks that the user is created
        self.assertListEqual(perms, [])

    # Staff Roles

    def test_create_staff_role(self):
        role = PermafrostRole(name="Bobs Staff Group", category="staff")
        role.save()
        role.users_add(self.staffuser)      # Add user to the Group
        perms = list(self.staffuser.get_all_permissions())

        self.assertEqual([perm.name for perm in role.group.permissions.all()], ['Can view Role'])   # Make sure the required permission is present in the group
        self.assertEqual(role.group.name, "1_staff_bobs-staff-group")        # Checks that the user is created
        self.assertListEqual(perms, ['permafrost.view_permafrostrole'])

    def test_add_optional_to_staff_role(self):
        '''
        Test that the optional role can be added
        '''
        role = PermafrostRole(name="Bobs Staff Group", category="staff")
        role.save()
        role.permissions_add(self.perm_change_permafrostrole)
        role.users_add(self.staffuser)      # Add user to the Group
        perms = list(self.staffuser.get_all_permissions())
        perms.sort()

        self.assertListEqual(list(role.group.permissions.all()), [self.perm_change_permafrostrole, self.perm_view_permafrostrole])            # Check the permissions on the group
        self.assertEqual(role.group.name, "1_staff_bobs-staff-group")        # Checks that the user is created
        self.assertListEqual(perms, ['permafrost.change_permafrostrole', 'permafrost.view_permafrostrole'])

    def test_add_not_allowed_to_staff_role(self):
        '''
        Test that a permission that is not optional or required can be added
        '''
        role = PermafrostRole(name="Bobs Staff Group", category="staff")
        role.save()
        role.permissions_add(self.perm_delete_permafrostrole)
        role.users_add(self.staffuser)
        perms = list(self.staffuser.get_all_permissions())

        self.assertEqual([perm.name for perm in role.group.permissions.all()], ['Can view Role'])   # Make sure the required permission is present in the group
        self.assertEqual(role.group.name, "1_staff_bobs-staff-group")        # Checks that the user is created
        self.assertListEqual(perms, ['permafrost.view_permafrostrole'])

    def test_clear_permissions_on_staff_role(self):
        role = PermafrostRole(name="Bobs Staff Group", category="staff")
        role.save()
        role.permissions_add(self.perm_view_permafrostrole)
        role.permissions_clear()
        role.users_add(self.staffuser)      # Add user to the Group
        perms = list(self.staffuser.get_all_permissions())

        self.assertEqual([perm.name for perm in role.group.permissions.all()], ['Can view Role'])   # Make sure the required permission is present in the group
        self.assertEqual(role.group.name, "1_staff_bobs-staff-group")        # Checks that the user is created
        self.assertListEqual(perms, ['permafrost.view_permafrostrole'])

    # Administration Roles

    def test_create_administration_role(self):
        role = PermafrostRole(name="Bobs Administration Group", category="administration")
        role.save()
        role.users_add(self.administrationuser)      # Add user to the Group
        perms = list(self.administrationuser.get_all_permissions())
        perms.sort()

        self.assertListEqual([perm.name for perm in role.group.permissions.all()], ['Can add Role', 'Can change Role', 'Can view Role'])   # Make sure the required permission is present in the group
        self.assertEqual(role.group.name, "1_administration_bobs-administration-group")        # Checks that the user is created
        self.assertListEqual(perms, ['permafrost.add_permafrostrole', 'permafrost.change_permafrostrole', 'permafrost.view_permafrostrole'])

    def test_add_optional_to_administration_role(self):
        role = PermafrostRole(name="Bobs Administration Group", category="administration")
        role.save()
        role.permissions_add(self.perm_delete_permafrostrole)
        role.users_add(self.administrationuser)      # Add user to the Group
        perms = list(self.administrationuser.get_all_permissions())
        perms.sort()

        self.assertListEqual([perm.name for perm in role.group.permissions.all()], ['Can add Role', 'Can change Role', 'Can delete Role', 'Can view Role'])   # Make sure the required permission is present in the group
        self.assertEqual(role.group.name, "1_administration_bobs-administration-group")        # Checks that the user is created
        self.assertListEqual(perms, ['permafrost.add_permafrostrole', 'permafrost.change_permafrostrole', 'permafrost.delete_permafrostrole', 'permafrost.view_permafrostrole'])

    def test_add_not_allowed_to_administration_role(self):
        role = PermafrostRole(name="Bobs Administration Group", category="administration")
        role.save()
        role.permissions_add(self.perm_add_logentry)
        role.permissions_add(self.perm_delete_permafrostrole)
        role.users_add(self.administrationuser)      # Add user to the Group
        perms = list(self.administrationuser.get_all_permissions())
        perms.sort()

        self.assertListEqual([perm.name for perm in role.group.permissions.all()], ['Can add Role', 'Can change Role', 'Can delete Role', 'Can view Role'])   # Make sure the required permission is present in the group
        self.assertEqual(role.group.name, "1_administration_bobs-administration-group")        # Checks that the user is created
        self.assertListEqual(perms, ['permafrost.add_permafrostrole', 'permafrost.change_permafrostrole', 'permafrost.delete_permafrostrole', 'permafrost.view_permafrostrole'])

    def test_clear_permissions_on_administration_role(self):
        role = PermafrostRole(name="Bobs Administration Group", category="administration")
        role.save()
        role.permissions_add(self.perm_view_permafrostrole)
        role.permissions_clear()
        role.users_add(self.administrationuser)      # Add user to the Group
        perms = list(self.administrationuser.get_all_permissions())
        perms.sort()

        self.assertListEqual([perm.name for perm in role.group.permissions.all()], ['Can add Role', 'Can change Role', 'Can view Role'])   # Make sure the required permission is present in the group
        self.assertEqual(role.group.name, "1_administration_bobs-administration-group")        # Checks that the user is created
        self.assertListEqual(perms, ['permafrost.add_permafrostrole', 'permafrost.change_permafrostrole', 'permafrost.view_permafrostrole'])

    # Test Role Creation Rules

    def test_create_duplicate_role(self):
        '''
        Test that creating a PermafrostRole of the same name producers and error
        '''
        role_a = PermafrostRole(name="Bobs Super Group", site=self.site_1, category="user")
        role_a.save()

        role_c = PermafrostRole(name="Bobs Super Group", site=self.site_2, category="user")
        role_c.save()

        with self.assertRaises(IntegrityError):

            with transaction.atomic():
                role_b = PermafrostRole(name="Bobs Super Group", site=self.site_2, category="user")
                role_b.save()

            with transaction.atomic():
                role_d = PermafrostRole(name="Bobs Super Group", site=self.site_2, category="staff")
                role_d.save()

    # Test that deleting a PermafrostRole deletes the matching group

    def test_delete_role_deletes_group(self):
        role = PermafrostRole(name="Awesome Students", category="user")
        role.save()

        group = role.group
        group_name = group.name

        self.assertEqual(role.group.name, "1_user_awesome-students")

        role.delete()

        with self.assertRaises(Group.DoesNotExist):
            group = Group.objects.get(name=group_name)


# Don't run the following tests if DRF is not loaded
@skipIf(SKIP_DRF_TESTS, "Django Rest Framework not installed, skipping tests")
class PermafrostAPITest(TestCase):

    fixtures = ['unit_test']

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='john', email='jlennon@beatles.com', password='Passw0rd!')
        self.staffuser = User.objects.create_user(username='staffy', email='staffy@beatles.com', password='Passw0rd!', is_active=True, is_staff=True, )
        self.adminuser = User.objects.create_user(username='adminy', email='adminy@beatles.com', password='Passw0rd!', is_active=True, is_staff=True, is_superuser=True)

        self.site_1 = Site.objects.get(pk=1)
        self.site_2 = Site.objects.get(pk=2)

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
