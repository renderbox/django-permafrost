import importlib
from unittest import skipIf
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.sites.models import Site
from django.core.exceptions import (
    ImproperlyConfigured,
    PermissionDenied,
    ValidationError,
)
from django.forms.models import model_to_dict
from django.test import RequestFactory, TestCase, override_settings
from django.test.client import Client
from django.test.utils import captured_stderr
from django.urls.base import resolve, reverse

from .api import services
from .backends import PermafrostModelBackend
from .checks import check_permafrost_settings
from .forms import (
    PermafrostRoleCreateForm,
    PermafrostRoleUpdateForm,
    RoleMembershipAddForm,
    RoleMembershipRemoveForm,
    SelectPermafrostRoleTypeForm,
)
from .permissions import has_all_permissions
from .views import (
    PermafrostRoleCreateView,
    PermafrostRoleListView,
    PermafrostRoleManageView,
    PermafrostRoleUpdateView,
    PermafrostRoleUsersView,
)

try:
    from drf_spectacular.validation import validate_schema
    from rest_framework.test import APIClient

    SKIP_DRF_TESTS = False
except ImportError:
    SKIP_DRF_TESTS = True

from permafrost.models import (
    CATEGORIES,
    PERMAFROST_EXCLUDED_ROLES,
    PermafrostRole,
    bounded_group_name,
    get_all_perms_for_all_categories,
    get_current_site,
)


class PermafrostRoleModelTest(TestCase):

    fixtures = ["unit_test"]

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="john", email="jlennon@beatles.com", password="Passw0rd!"
        )
        self.staffuser = User.objects.create_user(
            username="staffy", email="staffy@beatles.com", password="Passw0rd!"
        )
        self.administrationuser = User.objects.create_user(
            username="adminy", email="adminy@beatles.com", password="Passw0rd!"
        )

        self.site_1 = Site.objects.get(pk=1)
        self.site_2 = Site.objects.get(pk=2)

        self.perm_view_permafrostrole = Permission.objects.get_by_natural_key(
            *("view_permafrostrole", "permafrost", "permafrostrole")
        )
        self.perm_change_permafrostrole = Permission.objects.get_by_natural_key(
            *("change_permafrostrole", "permafrost", "permafrostrole")
        )
        self.perm_delete_permafrostrole = Permission.objects.get_by_natural_key(
            *("delete_permafrostrole", "permafrost", "permafrostrole")
        )
        self.perm_add_logentry = Permission.objects.get_by_natural_key(
            *("add_logentry", "admin", "logentry")
        )

    def test_role_rename_updates_group(self):
        """
        Make sure renaming the PermafrostRole properly renames the Django Group model.
        """
        role = PermafrostRole(name="Awesome Students", category="user")
        role.save()

        pk_check = role.group.pk
        self.assertEqual(role.group.name, "1_user_awesome-students")

        role.name = "OK Students"
        role.save()

        # new_role_group = Group.objects.get(name=role.get_group_name())

        self.assertEqual(role.group.name, "1_user_ok-students")
        self.assertEqual(
            role.group.pk, pk_check
        )  # Make sure a new group was not generated

    # User Roles

    def test_create_user_role(self):
        """
        Test that creating a PermafrostRole creates a matching Group
        """
        role = PermafrostRole(name="Bobs Super Group", category="user")
        role.save()
        role.users_add(self.user)
        perms = list(self.user.get_all_permissions())

        self.assertEqual(
            list(role.group.permissions.all()), []
        )  # Check the permissions on the group
        self.assertEqual(
            role.group.name, "1_user_bobs-super-group"
        )  # Checks that the user is created
        self.assertEqual(perms, [])

    def test_add_optional_to_user_role(self):
        """
        Test that the optional role can be added
        """
        role = PermafrostRole(name="Bobs Super Group", category="user")
        role.save()
        role.permissions_add(self.perm_view_permafrostrole)
        role.users_add(self.user)
        perms = list(self.user.get_all_permissions())

        self.assertListEqual(
            list(role.group.permissions.all()), [self.perm_view_permafrostrole]
        )  # Check the permissions on the group
        self.assertEqual(
            role.group.name, "1_user_bobs-super-group"
        )  # Checks that the user is created
        self.assertListEqual(perms, ["permafrost.view_permafrostrole"])

    def test_add_not_allowed_to_user_role(self):
        """
        Test that a permission that is not optional or required can be added
        """
        role = PermafrostRole(name="Bobs Super Group", category="user")
        role.save()
        role.permissions_add(self.perm_delete_permafrostrole)
        role.users_add(self.user)
        perms = list(self.user.get_all_permissions())

        self.assertEqual(
            list(role.group.permissions.all()), []
        )  # Check the permissions on the group
        self.assertEqual(
            role.group.name, "1_user_bobs-super-group"
        )  # Checks that the user is created
        self.assertListEqual(perms, [])

    def test_clear_permissions_on_user_role(self):
        """
        Test that clearning permissions restores them to just the required.
        """
        role = PermafrostRole(name="Bobs Super Group", category="user")
        role.save()
        role.permissions_add(self.perm_view_permafrostrole)
        role.permissions_clear()
        role.users_add(self.user)
        perms = list(self.user.get_all_permissions())

        self.assertEqual(
            list(role.group.permissions.all()), []
        )  # Check the permissions on the group
        self.assertEqual(
            role.group.name, "1_user_bobs-super-group"
        )  # Checks that the user is created
        self.assertListEqual(perms, [])

    # Staff Roles

    def test_create_staff_role(self):
        role = PermafrostRole(name="Created Staff Group", category="staff")
        role.save()
        role.users_add(self.staffuser)  # Add user to the Group
        perms = list(self.staffuser.get_all_permissions())

        self.assertEqual(
            [perm.codename for perm in role.group.permissions.all()],
            ["view_permafrostrole"],
        )  # Make sure the required permission is present in the group
        self.assertEqual(
            role.group.name, "1_staff_created-staff-group"
        )  # Checks that the user is created
        self.assertListEqual(perms, ["permafrost.view_permafrostrole"])

    def test_add_optional_to_staff_role(self):
        """
        Test that the optional role can be added
        """
        role = PermafrostRole(name="Optional Staff Group", category="staff")
        role.save()
        role.permissions_add(self.perm_change_permafrostrole)
        role.users_add(self.staffuser)  # Add user to the Group
        perms = list(self.staffuser.get_all_permissions())
        perms.sort()

        self.assertListEqual(
            list(role.group.permissions.all()),
            [self.perm_change_permafrostrole, self.perm_view_permafrostrole],
        )  # Check the permissions on the group
        self.assertEqual(
            role.group.name, "1_staff_optional-staff-group"
        )  # Checks that the user is created
        self.assertListEqual(
            perms,
            ["permafrost.change_permafrostrole", "permafrost.view_permafrostrole"],
        )

    def test_add_not_allowed_to_staff_role(self):
        """
        Test that a permission that is not optional or required can be added
        """
        role = PermafrostRole(name="Disallowed Staff Group", category="staff")
        role.save()
        role.permissions_add(self.perm_delete_permafrostrole)
        role.users_add(self.staffuser)
        perms = list(self.staffuser.get_all_permissions())

        self.assertEqual(
            [perm.codename for perm in role.group.permissions.all()],
            ["view_permafrostrole"],
        )  # Make sure the required permission is present in the group
        self.assertEqual(
            role.group.name, "1_staff_disallowed-staff-group"
        )  # Checks that the user is created
        self.assertListEqual(perms, ["permafrost.view_permafrostrole"])

    def test_clear_permissions_on_staff_role(self):
        role = PermafrostRole(name="Cleared Staff Group", category="staff")
        role.save()
        role.permissions_add(self.perm_view_permafrostrole)
        role.permissions_clear()
        role.users_add(self.staffuser)  # Add user to the Group
        perms = list(self.staffuser.get_all_permissions())

        self.assertEqual(
            [perm.codename for perm in role.group.permissions.all()],
            ["view_permafrostrole"],
        )  # Make sure the required permission is present in the group
        self.assertEqual(
            role.group.name, "1_staff_cleared-staff-group"
        )  # Checks that the user is created
        self.assertListEqual(perms, ["permafrost.view_permafrostrole"])

    # Administration Roles

    def test_create_administration_role(self):
        role = PermafrostRole(
            name="Bobs Administration Group", category="administration"
        )
        role.save()
        role.users_add(self.administrationuser)  # Add user to the Group
        perms = list(self.administrationuser.get_all_permissions())
        perms.sort()

        self.assertListEqual(
            [perm.codename for perm in role.group.permissions.all()],
            ["add_permafrostrole", "change_permafrostrole", "view_permafrostrole"],
        )  # Make sure the required permission is present in the group
        self.assertEqual(
            role.group.name, "1_administration_bobs-administration-group"
        )  # Checks that the user is created
        self.assertListEqual(
            perms,
            [
                "permafrost.add_permafrostrole",
                "permafrost.change_permafrostrole",
                "permafrost.view_permafrostrole",
            ],
        )

    def test_add_optional_to_administration_role(self):
        role = PermafrostRole(
            name="Bobs Administration Group", category="administration"
        )
        role.save()
        role.permissions_add(self.perm_delete_permafrostrole)
        role.users_add(self.administrationuser)  # Add user to the Group
        perms = list(self.administrationuser.get_all_permissions())
        perms.sort()

        self.assertListEqual(
            [perm.codename for perm in role.group.permissions.all()],
            [
                "add_permafrostrole",
                "change_permafrostrole",
                "delete_permafrostrole",
                "view_permafrostrole",
            ],
        )  # Make sure the required permission is present in the group
        self.assertEqual(
            role.group.name, "1_administration_bobs-administration-group"
        )  # Checks that the user is created
        self.assertListEqual(
            perms,
            [
                "permafrost.add_permafrostrole",
                "permafrost.change_permafrostrole",
                "permafrost.delete_permafrostrole",
                "permafrost.view_permafrostrole",
            ],
        )

    def test_add_not_allowed_to_administration_role(self):
        role = PermafrostRole(
            name="Bobs Administration Group", category="administration"
        )
        role.save()
        role.permissions_add(self.perm_add_logentry)
        role.permissions_add(self.perm_delete_permafrostrole)
        role.users_add(self.administrationuser)  # Add user to the Group
        perms = list(self.administrationuser.get_all_permissions())
        perms.sort()

        self.assertListEqual(
            [perm.codename for perm in role.group.permissions.all()],
            [
                "add_permafrostrole",
                "change_permafrostrole",
                "delete_permafrostrole",
                "view_permafrostrole",
            ],
        )  # Make sure the required permission is present in the group
        self.assertEqual(
            role.group.name, "1_administration_bobs-administration-group"
        )  # Checks that the user is created
        self.assertListEqual(
            perms,
            [
                "permafrost.add_permafrostrole",
                "permafrost.change_permafrostrole",
                "permafrost.delete_permafrostrole",
                "permafrost.view_permafrostrole",
            ],
        )

    def test_clear_permissions_on_administration_role(self):
        role = PermafrostRole(
            name="Bobs Administration Group", category="administration"
        )
        role.save()
        role.permissions_add(self.perm_view_permafrostrole)
        role.permissions_clear()
        role.users_add(self.administrationuser)  # Add user to the Group
        perms = list(self.administrationuser.get_all_permissions())
        perms.sort()

        self.assertListEqual(
            [perm.codename for perm in role.group.permissions.all()],
            ["add_permafrostrole", "change_permafrostrole", "view_permafrostrole"],
        )  # Make sure the required permission is present in the group
        self.assertEqual(
            role.group.name, "1_administration_bobs-administration-group"
        )  # Checks that the user is created
        self.assertListEqual(
            perms,
            [
                "permafrost.add_permafrostrole",
                "permafrost.change_permafrostrole",
                "permafrost.view_permafrostrole",
            ],
        )

    # Test Role Creation Rules

    def test_create_duplicate_role(self):
        """
        Test that creating a PermafrostRole of the same name producers and error
        """
        role_a = PermafrostRole(
            name="Bobs Super Group", site=self.site_1, category="user"
        )
        role_a.save()

        role_c = PermafrostRole(
            name="Bobs Super Group", site=self.site_2, category="user"
        )
        role_c.save()

        with self.assertRaises(ValidationError):
            role_b = PermafrostRole(
                name="Bobs Super Group", site=self.site_2, category="user"
            )
            role_b.save()

        with self.assertRaises(ValidationError):
            role_d = PermafrostRole(
                name="Bobs Super Group", site=self.site_2, category="staff"
            )
            role_d.save()

    def test_normalized_slug_collision_is_rejected_in_same_context(self):
        role = PermafrostRole(name="Support Team", category="user")
        role.save()
        group_count = Group.objects.count()

        with self.assertRaises(ValidationError):
            PermafrostRole(name="Support-Team", category="user").save()

        self.assertEqual(Group.objects.count(), group_count)

    def test_normalized_slug_is_allowed_in_different_contexts(self):
        role_a = PermafrostRole(
            name="Support Team",
            category="user",
            site=self.site_1,
        )
        role_a.save()
        role_b = PermafrostRole(
            name="Support-Team",
            category="user",
            site=self.site_2,
        )
        role_b.save()

        self.assertEqual(role_a.slug, role_b.slug)
        self.assertNotEqual(role_a.context_object_id, role_b.context_object_id)

    def test_role_rename_changes_slug_url_and_group_name(self):
        role = PermafrostRole(name="Original Role", category="user")
        role.save()
        original_url = role.get_absolute_url()

        role.name = "Renamed Role"
        role.save()

        self.assertEqual(role.slug, "renamed-role")
        self.assertNotEqual(role.get_absolute_url(), original_url)
        self.assertEqual(role.group.name, "1_user_renamed-role")

    def test_role_rename_collision_does_not_partially_apply(self):
        PermafrostRole(name="Support Team", category="user").save()
        role = PermafrostRole(name="Billing Team", category="user")
        role.save()
        original_group_name = role.group.name

        role.name = "Support-Team"
        with self.assertRaises(ValidationError):
            role.save()

        role.refresh_from_db()
        role.group.refresh_from_db()
        self.assertEqual(role.name, "Billing Team")
        self.assertEqual(role.slug, "billing-team")
        self.assertEqual(role.group.name, original_group_name)

    def test_role_name_must_produce_nonempty_slug(self):
        with self.assertRaises(ValidationError):
            PermafrostRole(name="!!!", category="user").save()

    def test_role_does_not_adopt_unrelated_group_with_generated_name(self):
        group = Group.objects.create(name="1_user_reserved-role")
        group.permissions.add(self.perm_add_logentry)

        with self.assertRaises(ValidationError):
            PermafrostRole(name="Reserved Role", category="user").save()

        group.refresh_from_db()
        self.assertIn(self.perm_add_logentry, group.permissions.all())
        self.assertFalse(PermafrostRole.objects.filter(name="Reserved Role").exists())

    def test_group_can_only_belong_to_one_role(self):
        role = PermafrostRole(name="Owned Group", category="user")
        role.save()

        with self.assertRaises(ValidationError):
            PermafrostRole(
                name="Second Group Owner",
                category="user",
                group=role.group,
            ).save()

    def test_bounded_group_names_are_stable_and_collision_resistant(self):
        long_name = "context_" + ("x" * 200)
        bounded_name = bounded_group_name(long_name)

        self.assertEqual(len(bounded_name), Group._meta.get_field("name").max_length)
        self.assertEqual(bounded_name, bounded_group_name(long_name))
        self.assertNotEqual(bounded_name, bounded_group_name(long_name + "y"))

    def test_role_defaults_to_site_context(self):
        role = PermafrostRole(name="Context Default Role", category="user")
        role.save()

        self.assertEqual(role.context, Site.objects.get_current())
        self.assertEqual(role.context_object_id, Site.objects.get_current().pk)
        self.assertEqual(role.get_group_name(), "1_user_context-default-role")

    @override_settings(PERMAFROST_CONTEXT_MODEL="auth.Group")
    def test_same_role_name_allowed_in_different_configured_contexts(self):
        context_a = Group.objects.create(name="Context A")
        context_b = Group.objects.create(name="Context B")

        role_a = PermafrostRole(name="Shared Role Name", category="user")
        role_a.set_context(context_a)
        role_a.save()

        role_b = PermafrostRole(name="Shared Role Name", category="user")
        role_b.set_context(context_b)
        role_b.save()

        self.assertEqual(role_a.context, context_a)
        self.assertEqual(role_b.context, context_b)
        self.assertNotEqual(role_a.get_group_name(), role_b.get_group_name())

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

    def test_get_all_perms_for_all_categories(self):
        all_perm_keys = [
            perm.natural_key() for perm in get_all_perms_for_all_categories()
        ]

        # grab all the permission natural keys from CATEGORIES in settings
        category_perm_keys = []
        for category, category_data in CATEGORIES.items():
            for optional_perm_data in category_data["optional"]:
                category_perm_keys.append(optional_perm_data["permission"])

            for optional_perm_data in category_data["required"]:
                category_perm_keys.append(optional_perm_data["permission"])

        self.assertListEqual(sorted(all_perm_keys), sorted(category_perm_keys))

    def test_unable_to_delete_default_roles(self):
        role = PermafrostRole.objects.get(pk=3)
        role.delete()
        role = PermafrostRole.objects.get(pk=3)
        self.assertFalse(role.deleted)


class PermafrostServiceAPITest(TestCase):
    fixtures = ["unit_test"]

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="service-user",
            email="service-user@example.com",
            password="Passw0rd!",
        )
        self.site_1 = Site.objects.get(pk=1)
        self.site_2 = Site.objects.get(pk=2)
        self.allowed_permission = Permission.objects.get_by_natural_key(
            *("view_permafrostrole", "permafrost", "permafrostrole")
        )
        self.disallowed_permission = Permission.objects.get_by_natural_key(
            *("add_logentry", "admin", "logentry")
        )

    def test_create_role_anchors_to_context(self):
        role = services.create_role(
            name="Service Role",
            category="user",
            context_object=self.site_2,
        )

        self.assertEqual(role.context, self.site_2)
        self.assertEqual(role.site, self.site_2)
        self.assertIn(role, services.list_roles(context_object=self.site_2))
        self.assertNotIn(role, services.list_roles(context_object=self.site_1))

    def test_role_queries_default_to_current_context(self):
        current_role = services.create_role(
            name="Current Context Role",
            category="user",
            context_object=self.site_1,
        )
        foreign_role = services.create_role(
            name="Foreign Context Role",
            category="user",
            context_object=self.site_2,
        )

        self.assertIn(current_role, services.list_roles())
        self.assertNotIn(foreign_role, services.list_roles())
        with self.assertRaises(PermafrostRole.DoesNotExist):
            services.get_role(foreign_role.slug)

    def test_set_role_permissions_rejects_disallowed_permissions(self):
        role = services.create_role(
            name="Service Permission Role",
            category="user",
            context_object=self.site_1,
        )

        with self.assertRaises(ValidationError):
            services.set_role_permissions(
                role,
                Permission.objects.filter(
                    id__in=[self.allowed_permission.id, self.disallowed_permission.id]
                ),
            )

        role_permission_ids = set(role.permissions().values_list("id", flat=True))
        self.assertNotIn(self.allowed_permission.id, role_permission_ids)
        self.assertNotIn(self.disallowed_permission.id, role_permission_ids)

    def test_add_and_remove_role_users(self):
        role = services.create_role(
            name="Service User Role",
            category="user",
            context_object=self.site_1,
        )

        services.add_role_users(role, [self.user])
        self.assertIn(self.user, role.user_set())

        services.remove_role_users(role, [self.user])
        self.assertNotIn(self.user, role.user_set())

    def test_unknown_permission_ids_raise_validation_error(self):
        with self.assertRaises(ValidationError):
            services.get_permissions_from_ids([999999])

    def test_create_role_does_not_partially_apply_disallowed_permissions(self):
        with self.assertRaises(ValidationError):
            services.create_role(
                name="Invalid Service Role",
                category="user",
                context_object=self.site_1,
                permissions=[self.disallowed_permission],
            )

        self.assertFalse(
            PermafrostRole.objects.filter(name="Invalid Service Role").exists()
        )

    def test_create_role_rolls_back_role_and_group_on_conform_failure(self):
        group_name = "1_user_rollback-create"

        with patch.object(
            PermafrostRole,
            "permissions_set",
            side_effect=RuntimeError("conform failed"),
        ):
            with self.assertRaises(RuntimeError):
                services.create_role(
                    name="Rollback Create",
                    category="user",
                    context_object=self.site_1,
                )

        self.assertFalse(PermafrostRole.objects.filter(name="Rollback Create").exists())
        self.assertFalse(Group.objects.filter(name=group_name).exists())

    def test_update_role_rolls_back_fields_on_conform_failure(self):
        role = services.create_role(
            name="Rollback Update",
            category="user",
            context_object=self.site_1,
        )

        with patch.object(
            role,
            "permissions_set",
            side_effect=RuntimeError("conform failed"),
        ):
            with self.assertRaises(RuntimeError):
                services.update_role(role, name="Partially Updated")

        role.refresh_from_db()
        role.group.refresh_from_db()
        self.assertEqual(role.name, "Rollback Update")
        self.assertEqual(role.group.name, "1_user_rollback-update")

    def test_unknown_user_ids_raise_validation_error(self):
        with self.assertRaises(ValidationError):
            services.get_users_from_ids([999999])

    @override_settings(PERMAFROST_API_USER_LOOKUP_FIELD="username")
    def test_users_can_be_resolved_by_configured_unique_identifier(self):
        users = services.get_users_from_identifiers([self.user.username])

        self.assertEqual(list(users), [self.user])

    @override_settings(PERMAFROST_API_USER_LOOKUP_FIELD="username")
    def test_unknown_user_identifiers_raise_validation_error(self):
        with self.assertRaises(ValidationError):
            services.get_users_from_identifiers(["not-a-user"])

    def test_user_identifier_lookup_requires_configuration(self):
        with self.assertRaises(ImproperlyConfigured):
            services.get_users_from_identifiers([self.user.username])

    def test_services_do_not_require_drf_imports(self):
        def guarded_import(name, *args, **kwargs):
            if name.startswith(("rest_framework", "drf_spectacular")):
                raise AssertionError(
                    "permafrost.api.services imported an optional HTTP API dependency"
                )
            return original_import(name, *args, **kwargs)

        original_import = __import__
        with patch("builtins.__import__", guarded_import):
            importlib.reload(services)

        importlib.reload(services)


# Don't run the following tests if DRF is not loaded
@skipIf(SKIP_DRF_TESTS, "Django Rest Framework not installed, skipping tests")
class PermafrostAPITest(TestCase):

    fixtures = ["unit_test"]

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="john", email="jlennon@beatles.com", password="Passw0rd!"
        )
        self.staffuser = User.objects.create_user(
            username="staffy",
            email="staffy@beatles.com",
            password="Passw0rd!",
            is_active=True,
            is_staff=True,
        )
        self.adminuser = User.objects.create_user(
            username="adminy",
            email="adminy@beatles.com",
            password="Passw0rd!",
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )

        self.site_1 = Site.objects.get(pk=1)
        self.site_2 = Site.objects.get(pk=2)

        self.client = APIClient()

    def test_superuser_can_access_permissions_endpoint(self):
        """
        Uses a user that has all the permissions.
        """
        self.client.force_authenticate(user=self.adminuser)
        response = self.client.get("/permissions/", format="json")
        assert response.status_code == 200

    def test_can_not_access_permissions_endpoint(self):
        """
        Uses a user that does not have the required permission
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/permissions/", format="json")
        assert response.status_code == 403

    def test_superuser_can_list_permafrost_roles_api(self):
        self.client.force_authenticate(user=self.adminuser)
        response = self.client.get("/api/permafrost/v1/roles/", format="json")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data)

    def test_anonymous_user_can_not_list_permafrost_roles_api(self):
        response = self.client.get("/api/permafrost/v1/roles/", format="json")

        self.assertEqual(response.status_code, 403)

    def test_api_v1_route_has_versioned_namespace(self):
        url = reverse("permafrost_api:v1:role-list")

        self.assertEqual(url, "/api/permafrost/v1/roles/")
        self.assertEqual(resolve(url).view_name, "permafrost_api:v1:role-list")

    def test_unversioned_api_route_is_not_exposed(self):
        self.client.force_authenticate(user=self.adminuser)

        response = self.client.get("/api/permafrost/roles/", format="json")

        self.assertEqual(response.status_code, 404)

    def test_openapi_schema_is_public_versioned_and_warning_free(self):
        schema_url = reverse("permafrost_api:v1:schema")

        with captured_stderr() as stderr:
            response = self.client.get(f"{schema_url}?format=json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(response.data["openapi"], "3.0.3")
        self.assertEqual(response.data["info"]["version"], "1.0.0")
        self.assertEqual(
            response.data["servers"],
            [
                {
                    "url": "/api/permafrost/v1/",
                    "description": "Permafrost v1 API",
                }
            ],
        )
        self.assertNotIn("/schema/", response.data["paths"])
        validate_schema(response.data)

    def test_openapi_schema_describes_custom_actions_and_examples(self):
        response = self.client.get(f'{reverse("permafrost_api:v1:schema")}?format=json')
        schema = response.data

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            schema["paths"]["/roles/{slug}/users/"]["delete"]["operationId"],
            "roles_users_bulk_remove",
        )
        self.assertEqual(
            schema["paths"]["/roles/{slug}/users/{user_id}/"]["delete"]["operationId"],
            "roles_users_remove",
        )
        self.assertIn(
            "RoleResponse",
            schema["paths"]["/roles/"]["post"]["responses"]["201"]["content"][
                "application/json"
            ]["examples"],
        )
        membership_examples = schema["paths"]["/roles/{slug}/users/"]["post"][
            "requestBody"
        ]["content"]["application/json"]["examples"]
        self.assertEqual(
            set(membership_examples),
            {"UsersByPrimaryKey", "UsersByConfiguredIdentifier"},
        )
        self.assertNotIn(
            "PaginatedCategoryList",
            schema["components"]["schemas"],
        )
        self.assertNotIn(
            "PaginatedPermissionList",
            schema["components"]["schemas"],
        )

    def test_api_list_only_returns_current_context_roles(self):
        self.client.force_authenticate(user=self.adminuser)
        site_1_role = PermafrostRole.objects.create(
            category="user", name="API Site One Role", site=self.site_1
        )
        site_2_role = PermafrostRole.objects.create(
            category="user", name="API Site Two Role", site=self.site_2
        )

        response = self.client.get("/api/permafrost/v1/roles/", format="json")
        returned_slugs = {role["slug"] for role in response.data["results"]}

        self.assertEqual(response.status_code, 200)
        self.assertIn(site_1_role.slug, returned_slugs)
        self.assertNotIn(site_2_role.slug, returned_slugs)

    def test_api_role_list_is_paginated(self):
        self.client.force_authenticate(user=self.adminuser)

        response = self.client.get(
            "/api/permafrost/v1/roles/?page_size=2",
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data),
            {"count", "next", "previous", "results"},
        )
        self.assertEqual(len(response.data["results"]), 2)
        self.assertGreaterEqual(response.data["count"], 2)

    def test_api_role_list_supports_search_filters_and_ordering(self):
        self.client.force_authenticate(user=self.adminuser)
        matching_role = PermafrostRole.objects.create(
            category="user",
            name="Zulu Query Target",
            site=self.site_1,
        )
        PermafrostRole.objects.create(
            category="staff",
            name="Alpha Query Target",
            site=self.site_1,
        )
        PermafrostRole.objects.create(
            category="user",
            name="Locked Query Target",
            locked=True,
            site=self.site_1,
        )

        response = self.client.get(
            "/api/permafrost/v1/roles/"
            "?search=Query+Target&category=user&locked=false&ordering=-name",
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["slug"], matching_role.slug)

    def test_api_role_list_rejects_invalid_locked_filter(self):
        self.client.force_authenticate(user=self.adminuser)

        response = self.client.get(
            "/api/permafrost/v1/roles/?locked=sometimes",
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("locked", response.data)

    def test_superuser_can_create_permafrost_role_api(self):
        self.client.force_authenticate(user=self.adminuser)
        response = self.client.post(
            "/api/permafrost/v1/roles/",
            data={"name": "API Role", "description": "", "category": "user"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "API Role")
        self.assertEqual(response.data["slug"], "api-role")
        role = PermafrostRole.objects.get(slug="api-role")
        self.assertEqual(role.context, Site.objects.get_current())

    def test_api_returns_400_for_invalid_category(self):
        self.client.force_authenticate(user=self.adminuser)
        response = self.client.post(
            "/api/permafrost/v1/roles/",
            data={"name": "Bad API Role", "description": "", "category": "missing"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("category", response.data)

    def test_api_returns_400_for_normalized_slug_collision(self):
        self.client.force_authenticate(user=self.adminuser)
        PermafrostRole.objects.create(
            category="user",
            name="API Support Team",
            site=self.site_1,
        )

        response = self.client.post(
            "/api/permafrost/v1/roles/",
            data={
                "name": "API-Support-Team",
                "description": "",
                "category": "user",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.data)

    def test_api_role_category_can_not_be_changed_after_create(self):
        self.client.force_authenticate(user=self.adminuser)
        role = PermafrostRole.objects.create(
            category="user",
            name="API Immutable Category",
            site=Site.objects.get_current(),
        )

        response = self.client.patch(
            f"/api/permafrost/v1/roles/{role.slug}/",
            data={"category": "staff"},
            format="json",
        )

        role.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(role.category, "user")
        self.assertIn("category", response.data)

    def test_api_permission_update_rejects_disallowed_permissions(self):
        self.client.force_authenticate(user=self.adminuser)
        role = PermafrostRole.objects.create(
            category="user", name="API Permission Role", site=Site.objects.get_current()
        )
        allowed_permission = Permission.objects.get_by_natural_key(
            *("view_permafrostrole", "permafrost", "permafrostrole")
        )
        disallowed_permission = Permission.objects.get_by_natural_key(
            *("add_logentry", "admin", "logentry")
        )

        response = self.client.put(
            f"/api/permafrost/v1/roles/{role.slug}/permissions/",
            data={
                "permission_ids": [
                    allowed_permission.id,
                    disallowed_permission.id,
                ]
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("permission_ids", response.data)
        role_permission_ids = set(role.permissions().values_list("id", flat=True))
        self.assertNotIn(allowed_permission.id, role_permission_ids)
        self.assertNotIn(disallowed_permission.id, role_permission_ids)

    def test_api_permission_update_returns_400_for_unknown_permission_ids(self):
        self.client.force_authenticate(user=self.adminuser)
        role = PermafrostRole.objects.create(
            category="user",
            name="API Unknown Permission",
            site=Site.objects.get_current(),
        )

        response = self.client.put(
            f"/api/permafrost/v1/roles/{role.slug}/permissions/",
            data={"permission_ids": [999999]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("permission_ids", response.data)

    def test_api_can_add_and_remove_role_users(self):
        self.client.force_authenticate(user=self.adminuser)
        role = PermafrostRole.objects.create(
            category="user", name="API User Role", site=Site.objects.get_current()
        )

        response = self.client.post(
            f"/api/permafrost/v1/roles/{role.slug}/users/",
            data={"user_ids": [self.user.id]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.user, role.user_set())

        response = self.client.delete(
            f"/api/permafrost/v1/roles/{role.slug}/users/{self.user.id}/",
            format="json",
        )

        self.assertEqual(response.status_code, 204)
        self.assertNotIn(self.user, role.user_set())

    def test_api_user_list_supports_pagination_search_and_ordering(self):
        self.client.force_authenticate(user=self.adminuser)
        role = PermafrostRole.objects.create(
            category="user",
            name="API User Query Role",
            site=self.site_1,
        )
        alpha_user = get_user_model().objects.create_user(
            username="alpha-member",
            email="alpha-member@example.com",
            password="Passw0rd!",
        )
        zulu_user = get_user_model().objects.create_user(
            username="zulu-member",
            email="zulu-member@example.com",
            password="Passw0rd!",
        )
        role.users_add(alpha_user, zulu_user)

        response = self.client.get(
            f"/api/permafrost/v1/roles/{role.slug}/users/"
            "?ordering=-username&page_size=1",
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["username"], "zulu-member")

        response = self.client.get(
            f"/api/permafrost/v1/roles/{role.slug}/users/?search=alpha-member",
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], alpha_user.pk)

    def test_api_user_list_rejects_invalid_ordering(self):
        self.client.force_authenticate(user=self.adminuser)
        role = PermafrostRole.objects.create(
            category="user",
            name="API Invalid User Ordering",
            site=self.site_1,
        )

        response = self.client.get(
            f"/api/permafrost/v1/roles/{role.slug}/users/?ordering=is_superuser",
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("ordering", response.data)

    def test_api_add_users_returns_400_for_unknown_user_ids(self):
        self.client.force_authenticate(user=self.adminuser)
        role = PermafrostRole.objects.create(
            category="user", name="API Unknown User", site=Site.objects.get_current()
        )

        response = self.client.post(
            f"/api/permafrost/v1/roles/{role.slug}/users/",
            data={"user_ids": [999999]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("user_ids", response.data)

    @override_settings(PERMAFROST_API_USER_LOOKUP_FIELD="username")
    def test_api_can_add_and_remove_role_users_by_configured_identifier(self):
        self.client.force_authenticate(user=self.adminuser)
        role = PermafrostRole.objects.create(
            category="user",
            name="API Identifier User",
            site=Site.objects.get_current(),
        )

        response = self.client.post(
            f"/api/permafrost/v1/roles/{role.slug}/users/",
            data={"user_identifiers": [self.user.username]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.user, role.user_set())

        response = self.client.delete(
            f"/api/permafrost/v1/roles/{role.slug}/users/",
            data={"user_identifiers": [self.user.username]},
            format="json",
        )

        self.assertEqual(response.status_code, 204)
        self.assertNotIn(self.user, role.user_set())

    def test_api_rejects_user_identifiers_when_lookup_is_not_configured(self):
        self.client.force_authenticate(user=self.adminuser)
        role = PermafrostRole.objects.create(
            category="user",
            name="API Disabled Identifier",
            site=Site.objects.get_current(),
        )

        response = self.client.post(
            f"/api/permafrost/v1/roles/{role.slug}/users/",
            data={"user_identifiers": [self.user.username]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("user_identifiers", response.data)

    @override_settings(PERMAFROST_API_USER_LOOKUP_FIELD="username")
    def test_api_rejects_mixed_user_ids_and_identifiers(self):
        self.client.force_authenticate(user=self.adminuser)
        role = PermafrostRole.objects.create(
            category="user",
            name="API Mixed Identifier",
            site=Site.objects.get_current(),
        )

        response = self.client.post(
            f"/api/permafrost/v1/roles/{role.slug}/users/",
            data={
                "user_ids": [self.user.pk],
                "user_identifiers": [self.user.username],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertNotIn(self.user, role.user_set())

    @override_settings(PERMAFROST_API_USER_LOOKUP_FIELD="username")
    def test_api_unknown_user_identifier_does_not_partially_add_memberships(self):
        self.client.force_authenticate(user=self.adminuser)
        role = PermafrostRole.objects.create(
            category="user",
            name="API Unknown Identifier",
            site=Site.objects.get_current(),
        )

        response = self.client.post(
            f"/api/permafrost/v1/roles/{role.slug}/users/",
            data={
                "user_identifiers": [self.user.username, "not-a-user"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("user_identifiers", response.data)
        self.assertNotIn(self.user, role.user_set())

    def test_api_bulk_user_removal_requires_membership_permission(self):
        role = PermafrostRole.objects.create(
            category="user",
            name="API Protected Bulk Removal",
            site=Site.objects.get_current(),
        )
        role.users_add(self.staffuser)
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(
            f"/api/permafrost/v1/roles/{role.slug}/users/",
            data={"user_ids": [self.staffuser.pk]},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn(self.staffuser, role.user_set())

    def test_api_remove_unknown_user_returns_404(self):
        self.client.force_authenticate(user=self.adminuser)
        role = PermafrostRole.objects.create(
            category="user",
            name="API Remove Unknown User",
            site=Site.objects.get_current(),
        )

        response = self.client.delete(
            f"/api/permafrost/v1/roles/{role.slug}/users/999999/",
            format="json",
        )

        self.assertEqual(response.status_code, 404)

    def test_api_delete_soft_deletes_role(self):
        self.client.force_authenticate(user=self.adminuser)
        role = PermafrostRole.objects.create(
            category="user", name="API Soft Delete", site=Site.objects.get_current()
        )

        response = self.client.delete(
            f"/api/permafrost/v1/roles/{role.slug}/",
            format="json",
        )

        role.refresh_from_db()
        self.assertEqual(response.status_code, 204)
        self.assertTrue(role.deleted)

    def test_api_delete_does_not_soft_delete_locked_role(self):
        self.client.force_authenticate(user=self.adminuser)
        role = PermafrostRole.objects.create(
            category="user",
            name="API Locked Delete",
            locked=True,
            site=Site.objects.get_current(),
        )

        response = self.client.delete(
            f"/api/permafrost/v1/roles/{role.slug}/",
            format="json",
        )

        role.refresh_from_db()
        self.assertEqual(response.status_code, 204)
        self.assertFalse(role.deleted)

    def test_api_object_routes_reject_foreign_context_slug(self):
        self.client.force_authenticate(user=self.adminuser)
        foreign_role = PermafrostRole.objects.create(
            category="user",
            name="Foreign API Role",
            site=self.site_2,
        )
        original_permission_ids = set(
            foreign_role.permissions().values_list("id", flat=True)
        )

        requests = [
            ("get", f"/api/permafrost/v1/roles/{foreign_role.slug}/", None),
            (
                "patch",
                f"/api/permafrost/v1/roles/{foreign_role.slug}/",
                {"name": "Cross Context Rename"},
            ),
            ("delete", f"/api/permafrost/v1/roles/{foreign_role.slug}/", None),
            (
                "get",
                f"/api/permafrost/v1/roles/{foreign_role.slug}/permissions/",
                None,
            ),
            (
                "put",
                f"/api/permafrost/v1/roles/{foreign_role.slug}/permissions/",
                {"permission_ids": []},
            ),
            (
                "get",
                f"/api/permafrost/v1/roles/{foreign_role.slug}/users/",
                None,
            ),
            (
                "post",
                f"/api/permafrost/v1/roles/{foreign_role.slug}/users/",
                {"user_ids": [self.user.pk]},
            ),
            (
                "delete",
                f"/api/permafrost/v1/roles/{foreign_role.slug}/users/{self.user.pk}/",
                None,
            ),
        ]

        for method, url, data in requests:
            with self.subTest(method=method, url=url):
                response = getattr(self.client, method)(url, data=data, format="json")
                self.assertEqual(response.status_code, 404)

        foreign_role.refresh_from_db()
        self.assertEqual(foreign_role.name, "Foreign API Role")
        self.assertFalse(foreign_role.deleted)
        self.assertNotIn(self.user, foreign_role.user_set())
        self.assertEqual(
            set(foreign_role.permissions().values_list("id", flat=True)),
            original_permission_ids,
        )


# @tag('admin_tests')
class PermafrostViewTests(TestCase):
    fixtures = ["unit_test"]

    def setUp(self):
        self.client = Client()
        self.pf_role = PermafrostRole.objects.create(
            category="staff", name="Test Role", site=Site.objects.get_current()
        )
        PermafrostRole.objects.create(
            category="staff", name="Test Role", site=Site.objects.get(pk=2)
        )
        self.super_user = get_user_model().objects.get(pk=1)
        self.client.force_login(self.super_user)

    def test_permafrost_base_url_resolves(self):
        found = resolve("/permafrost/")
        self.assertEqual(found.view_name, "permafrost:role-list")
        self.assertEqual(found.func.view_class, PermafrostRoleListView)

    def test_permafrost_manage_base_url_resolves(self):
        found = resolve("/permafrost/manage/")
        self.assertEqual(found.view_name, "permafrost:roles-manage")
        self.assertEqual(found.func.view_class, PermafrostRoleManageView)

    def test_role_users_url_resolves(self):
        found = resolve(f"/permafrost/role/{self.pf_role.slug}/users/")
        self.assertEqual(found.view_name, "permafrost:role-users")
        self.assertEqual(found.func.view_class, PermafrostRoleUsersView)

    def test_role_users_page_lists_current_members(self):
        member = get_user_model().objects.create_user(
            username="membership-list-user",
            email="membership-list@example.com",
            password="Passw0rd!",
        )
        self.pf_role.users_add(member)

        response = self.client.get(
            reverse("permafrost:role-users", kwargs={"slug": self.pf_role.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "permafrost/permafrostrole_users.html")
        self.assertContains(response, member.get_username())
        self.assertContains(response, member.email)
        self.assertIsInstance(response.context["add_form"], RoleMembershipAddForm)
        self.assertIsInstance(response.context["remove_form"], RoleMembershipRemoveForm)

    @override_settings(PERMAFROST_UI_PAGE_SIZE=1)
    def test_role_users_page_supports_search_and_pagination(self):
        alpha = get_user_model().objects.create_user(
            username="alpha-membership-user", password="Passw0rd!"
        )
        zulu = get_user_model().objects.create_user(
            username="zulu-membership-user", password="Passw0rd!"
        )
        self.pf_role.users_add(alpha, zulu)
        url = reverse("permafrost:role-users", kwargs={"slug": self.pf_role.slug})

        first_page = self.client.get(url)
        self.assertTrue(first_page.context["is_paginated"])
        self.assertEqual(first_page.context["paginator"].per_page, 1)
        self.assertContains(first_page, alpha.get_username())
        self.assertNotContains(first_page, zulu.get_username())

        search_response = self.client.get(url, {"q": "zulu-membership"})
        self.assertContains(search_response, zulu.get_username())
        self.assertNotContains(search_response, alpha.get_username())

    @override_settings(PERMAFROST_API_USER_LOOKUP_FIELD="username")
    def test_role_users_page_adds_members_by_configured_identifier(self):
        user = get_user_model().objects.create_user(
            username="membership-add-user", password="Passw0rd!"
        )
        url = reverse("permafrost:role-users", kwargs={"slug": self.pf_role.slug})

        response = self.client.post(
            url,
            {"action": "add", "identifiers": user.username},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(user, self.pf_role.user_set())
        self.assertContains(response, "Added 1 user to this role.")

    def test_role_users_page_adds_members_by_primary_key_by_default(self):
        user = get_user_model().objects.create_user(
            username="membership-id-user", password="Passw0rd!"
        )
        url = reverse("permafrost:role-users", kwargs={"slug": self.pf_role.slug})

        self.client.post(url, {"action": "add", "identifiers": str(user.pk)})

        self.assertIn(user, self.pf_role.user_set())

    def test_role_users_page_rejects_nonnumeric_primary_keys(self):
        url = reverse("permafrost:role-users", kwargs={"slug": self.pf_role.slug})

        response = self.client.post(
            url, {"action": "add", "identifiers": "not-a-primary-key"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter numeric user IDs.")

    def test_role_users_page_bulk_removes_current_members(self):
        first_user = get_user_model().objects.create_user(
            username="membership-remove-one", password="Passw0rd!"
        )
        second_user = get_user_model().objects.create_user(
            username="membership-remove-two", password="Passw0rd!"
        )
        self.pf_role.users_add(first_user, second_user)
        url = reverse("permafrost:role-users", kwargs={"slug": self.pf_role.slug})

        response = self.client.post(
            url,
            {
                "action": "remove",
                "users": [str(first_user.pk), str(second_user.pk)],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(first_user, self.pf_role.user_set())
        self.assertNotIn(second_user, self.pf_role.user_set())
        self.assertContains(response, "Removed 2 users from this role.")

    def test_role_users_page_requires_membership_permission_for_changes(self):
        operator = get_user_model().objects.create_user(
            username="membership-view-only", password="Passw0rd!"
        )
        candidate = get_user_model().objects.create_user(
            username="membership-candidate", password="Passw0rd!"
        )
        self.pf_role.users_add(operator)
        self.client.force_login(operator)
        url = reverse("permafrost:role-users", kwargs={"slug": self.pf_role.slug})

        get_response = self.client.get(url)
        post_response = self.client.post(
            url, {"action": "add", "identifiers": str(candidate.pk)}
        )

        self.assertEqual(get_response.status_code, 200)
        self.assertNotContains(get_response, 'name="action" value="add"')
        self.assertNotContains(get_response, 'name="action" value="remove"')
        self.assertEqual(post_response.status_code, 403)
        self.assertNotIn(candidate, self.pf_role.user_set())

    @override_settings(PERMAFROST_API_USER_LOOKUP_FIELD="username")
    def test_role_users_page_rejects_unknown_identifiers_without_partial_add(self):
        user = get_user_model().objects.create_user(
            username="known-membership-user", password="Passw0rd!"
        )
        url = reverse("permafrost:role-users", kwargs={"slug": self.pf_role.slug})

        response = self.client.post(
            url,
            {
                "action": "add",
                "identifiers": f"{user.username}, missing-membership-user",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unknown user identifiers")
        self.assertNotIn(user, self.pf_role.user_set())

    def test_role_users_page_does_not_expose_roles_from_another_context(self):
        foreign_role = PermafrostRole.objects.create(
            category="staff",
            name="Foreign Membership Role",
            site=Site.objects.get(pk=2),
        )
        url = reverse("permafrost:role-users", kwargs={"slug": foreign_role.slug})

        with override_settings(SITE_ID=1):
            Site.objects.clear_cache()
            response = self.client.get(url)
            post_response = self.client.post(
                url, {"action": "add", "identifiers": str(self.super_user.pk)}
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(post_response.status_code, 404)
        self.assertNotIn(self.super_user, foreign_role.user_set())

    def test_permaforst_manage_single_role_object_in_context(self):
        uri = reverse("permafrost:roles-manage")
        response = self.client.get(uri)
        self.assertIn("object", response.context)
        self.assertEqual(
            response.context["object"], PermafrostRole.on_site.all().first()
        )

    def test_manage_permafrost_roles_returns_correct_template(self):
        uri = reverse("permafrost:roles-manage")
        response = self.client.get(uri)
        # objects = PermafrostRole.on_site.all()
        # default_role = objects.first()
        self.assertTemplateUsed(response, "permafrost/base.html")
        self.assertTemplateUsed(response, "permafrost/permafrostrole_manage.html")

    def test_permafrostrole_manage_template_displays_list_of_roles_on_site(self):
        uri = reverse("permafrost:roles-manage")
        import html

        response = self.client.get(uri)
        objects = PermafrostRole.on_site.all()
        objects = objects.exclude(name__in=PERMAFROST_EXCLUDED_ROLES)

        self.assertTrue(len(objects))

        for object in objects:
            self.assertContains(response, html.escape(f"{object}"))

    def test_permafrostrole_manage_template_displays_selected_role_details(self):
        uri = reverse("permafrost:roles-manage")
        response = self.client.get(uri)
        default_role = PermafrostRole.on_site.first()
        self.assertContains(response, f"<h2>{default_role.name}</h2>")
        self.assertContains(
            response,
            f'<p>Role Type: <span class="font-weight-bold">{default_role.get_category_display()}</span></p>',
        )
        self.assertContains(response, f"<p>{default_role.description}</p>")

    def test_permafrostrole_manage_template_displays_selected_role_permissions(self):
        ## arrange
        default_role = PermafrostRole.on_site.first()
        optional_permission = Permission.objects.get_by_natural_key(
            *("view_permafrostrole", "permafrost", "permafrostrole")
        )
        default_role.permissions_add(optional_permission)
        ## act
        uri = reverse("permafrost:roles-manage")
        response = self.client.get(uri)
        ## assert
        self.assertEqual(len(default_role.permissions().all()), 2)

        for permission in default_role.permissions().all():
            if permission.id in default_role.all_perm_ids():
                self.assertContains(response, f"{permission.name}")

    def test_permafrostrole_manage_template_hides_selected_role_permissions_not_in_permafrost_categories(
        self,
    ):
        ## arrange
        default_role = PermafrostRole.on_site.first()
        ## act
        uri = reverse("permafrost:roles-manage")
        response = self.client.get(uri)
        ## assert
        self.assertEqual(len(default_role.permissions().all()), 1)

        for permission in default_role.permissions().all():
            if permission.id not in default_role.all_perm_ids():
                self.assertNotContains(response, f"{permission.name}")

    def test_list_view_returns_roles_on_current_site(self):
        uri = reverse("permafrost:role-list")
        response = self.client.get(uri)
        site_id = get_current_site()

        try:
            roles = response.context["object_list"]
            self.assertTrue(all(role.site.id == site_id for role in roles))
        except Exception as e:
            print("Returned site ids")  # TODO: Should revisit this error handling
            print([role.site.id for role in response.context["object_list"]])
            print("Error: " + str(e))
            print("")
            pass
        pass

    def test_list_view_excludes_deleted_roles_on_current_site(self):
        uri = reverse("permafrost:role-list")
        response = self.client.get(uri)
        PermafrostRole.objects.get(pk=2).delete()
        try:
            roles = response.context["object_list"]
            self.assertEqual(len(roles), 4)
        except Exception as e:
            print("Returned site ids")
            print([role.site.id for role in response.context["object_list"]])
            print("Error: " + str(e))
            print("")
            pass
        pass

    def test_administration_create_url_resolves(self):
        found = resolve("/permafrost/role/create/")
        self.assertEqual(found.view_name, "permafrost:role-create")
        self.assertEqual(found.func.view_class, PermafrostRoleCreateView)

    def test_administration_create_url_response_with_correct_template(self):
        url = reverse("permafrost:role-create")
        response = self.client.get(url)
        ## ensure _create.html extends the base template
        self.assertTemplateUsed(response, "permafrost/base.html")

        self.assertTemplateUsed(response, "permafrost/permafrostrole_form.html")

    def test_select_role_type_form_renders_on_GET(self):
        url = reverse("permafrost:role-create")
        response = self.client.get(url)
        try:
            self.assertContains(response, "Create Role")
            self.assertContains(response, 'id="role_form"')
            self.assertContains(response, 'name="name"')
            self.assertContains(response, 'name="description"')
            self.assertContains(response, 'name="category"')

            self.assertIsInstance(
                response.context["form"], SelectPermafrostRoleTypeForm
            )
        except Exception as e:
            print("")
            print(response.content.decode())
            print("Error: " + str(e))
            raise

    def test_role_edit_url_resolves(self):
        found = resolve(f"/permafrost/role/{self.pf_role.slug}/update/")
        self.assertEqual(found.view_name, "permafrost:role-update")
        self.assertEqual(found.func.view_class, PermafrostRoleUpdateView)

    def test_administration_edit_url_response_with_correct_template(self):
        url = reverse("permafrost:role-update", kwargs={"slug": self.pf_role.slug})
        response = self.client.get(url)
        ## ensure _create.html extends the base template
        self.assertTemplateUsed(response, "permafrost/base.html")

        self.assertTemplateUsed(response, "permafrost/permafrostrole_form.html")

    def test_update_role_form_renders_on_GET(self):
        url = reverse("permafrost:role-update", kwargs={"slug": self.pf_role.slug})
        response = self.client.get(url)
        try:
            self.assertContains(response, "Edit Permissions: Test Role")
            self.assertContains(response, 'id="role_form"')
            self.assertContains(response, 'name="name"')
            self.assertContains(response, 'name="description"')
            self.assertContains(response, 'name="category"')
            self.assertContains(response, 'name="permissions"')

            ## add deleted field down the line
            # self.assertContains(response, 'name="deleted"')

            self.assertIsInstance(response.context["form"], PermafrostRoleUpdateForm)
        except Exception as e:
            print("")
            print(response.content.decode())
            print("Error: " + str(e))
            raise

    def test_role_update_resolves(self):
        found = resolve("/permafrost/role/test-role/update/")
        self.assertEqual(found.view_name, "permafrost:role-update")
        self.assertEqual(found.func.view_class, PermafrostRoleUpdateView)

    def test_role_update_GET_returns_correct_template(self):
        uri = reverse("permafrost:role-update", kwargs={"slug": "test-role"})
        response = self.client.get(uri)
        self.assertTemplateUsed(response, "permafrost/base.html")
        self.assertTemplateUsed(response, "permafrost/permafrostrole_form.html")

    def test_update_form_has_selected_optional_permission(self):
        ## add optional permissions
        add_permission = Permission.objects.get_by_natural_key(
            *("add_permafrostrole", "permafrost", "permafrostrole")
        )
        change_permission = Permission.objects.get_by_natural_key(
            *("change_permafrostrole", "permafrost", "permafrostrole")
        )
        self.pf_role.permissions_set(
            Permission.objects.filter(
                codename__in=["add_permafrostrole", "change_permafrostrole"]
            )
        )

        uri = reverse("permafrost:role-update", kwargs={"slug": "test-role"})
        response = self.client.get(uri)
        try:
            self.assertTrue(
                response.context["permission_categories"]["permafrostrole"]["optional"][
                    0
                ].selected
            )
            self.assertTrue(
                response.context["permission_categories"]["permafrostrole"]["optional"][
                    1
                ].selected
            )
            self.assertEqual(
                response.context["permission_categories"]["permafrostrole"]["optional"][
                    0
                ].id,
                add_permission.id,
            )
            self.assertEqual(
                response.context["permission_categories"]["permafrostrole"]["optional"][
                    1
                ].id,
                change_permission.id,
            )
            self.assertEqual(
                response.context["permission_categories"]["permafrostrole"]["optional"][
                    0
                ].codename,
                "add_permafrostrole",
            )
            self.assertEqual(
                response.context["permission_categories"]["permafrostrole"]["optional"][
                    1
                ].codename,
                "change_permafrostrole",
            )
            self.assertContains(response, f'value="{add_permission.id}"')
            self.assertContains(response, f'value="{change_permission.id}"')
            self.assertContains(response, f'id="permission-{add_permission.id}"')
            self.assertContains(response, f'id="permission-{change_permission.id}"')
            self.assertContains(response, "checked")

        except Exception as e:
            print("")
            print(response.content.decode())
            print("Error: " + str(e))
            print("")
            raise

    def test_role_detail_GET_returns_404_if_not_on_current_site(self):
        uri = reverse("permafrost:role-update", kwargs={"slug": "administrator"})
        response = self.client.get(uri)
        try:
            self.assertContains(response, "Not Found", status_code=404)
        except Exception as e:
            print("")
            print(response.content.decode())
            print("Error: " + str(e))
            raise

    def test_role_update_POST_updates_name(self):
        uri = reverse("permafrost:role-update", kwargs={"slug": "test-role"})
        response = self.client.post(uri, data={"name": "Test Change"}, follow=True)
        self.assertContains(response, "Test Change")
        updated_role = PermafrostRole.objects.get(pk=self.pf_role.pk)
        self.assertEqual(updated_role.name, "Test Change")

    def test_role_update_POST_updates_when_no_values_are_changed(self):
        uri = reverse("permafrost:role-update", kwargs={"slug": "test-role"})

        request = RequestFactory().post(uri, data={"name": "Test Role"}, follow=True)

        request.user = self.super_user
        request.site = Site.objects.get(pk=2)
        response = PermafrostRoleUpdateView.as_view()(request, slug="test-role")
        response.client = self.client
        self.assertRedirects(response, "/permafrost/role/test-role/")
        # updated_role = PermafrostRole.objects.get(pk=self.pf_role.pk)

    def test_optional_permissions_are_updated_on_POST(self):
        ## ensure role currently has no optional permissions
        allowed_optional_permission_ids = [
            permission.id for permission in self.pf_role.optional_permissions()
        ]
        current_permission_ids = [
            permission.id for permission in self.pf_role.permissions().all()
        ]
        current_optional_permission_ids = [
            id for id in current_permission_ids if id in allowed_optional_permission_ids
        ]

        self.assertFalse(current_optional_permission_ids)

        uri = reverse("permafrost:role-update", kwargs={"slug": "test-role"})
        data = model_to_dict(self.pf_role)
        add_permission = Permission.objects.get_by_natural_key(
            *("add_permafrostrole", "permafrost", "permafrostrole")
        )
        change_permission = Permission.objects.get_by_natural_key(
            *("change_permafrostrole", "permafrost", "permafrostrole")
        )
        data.update(
            {"permissions": [str(add_permission.id), str(change_permission.id)]}
        )
        ## listcomp below used to remove 'description': None
        post_data = {k: v for k, v in data.items() if v is not None}
        self.client.post(uri, data=post_data, follow=True)

        updated_permission_ids_1 = [
            permission.id
            for permission in self.pf_role.permissions().all()
            if permission.id in allowed_optional_permission_ids
        ]

        self.assertEqual(
            sorted(updated_permission_ids_1),
            sorted([add_permission.id, change_permission.id]),
        )

        ## remove one permission

        data.update({"permissions": [str(add_permission.id)]})
        ## listcomp below used to remove 'description': None
        post_data = {k: v for k, v in data.items() if v is not None}
        self.client.post(uri, data=post_data, follow=True)

        updated_permission_ids_2 = [
            permission.id
            for permission in self.pf_role.permissions().all()
            if permission.id in allowed_optional_permission_ids
        ]

        self.assertEqual(updated_permission_ids_2, [add_permission.id])

    def test_optional_permissions_are_removed_when_empty_array_submitted_to_POST(self):
        ## arrange: add optional permissions
        self.pf_role.permissions_set(
            Permission.objects.filter(
                codename__in=["add_permafrostrole", "change_permafrostrole"]
            )
        )

        ## ensure optional role count is 2
        allowed_optional_permission_ids = [
            permission.id for permission in self.pf_role.optional_permissions()
        ]
        current_permission_ids = [
            permission.id for permission in self.pf_role.permissions().all()
        ]
        current_optional_permission_ids = [
            id for id in current_permission_ids if id in allowed_optional_permission_ids
        ]
        self.assertEqual(len(current_optional_permission_ids), 2)

        uri = reverse("permafrost:role-update", kwargs={"slug": "test-role"})
        data = model_to_dict(self.pf_role)
        data.update({"optional_staff_perms": []})
        ## iterator below used to remove 'description': None
        data = {k: v for k, v in data.items() if v is not None}
        response = self.client.post(uri, data=data, follow=True)

        updated_permission_ids = [
            permission.id
            for permission in self.pf_role.permissions().all()
            if permission.id in allowed_optional_permission_ids
        ]
        try:
            self.assertEqual(updated_permission_ids, [])
        except Exception as e:
            print("")
            print(response.content.decode())
            print("Error: " + str(e))
            print("")
            raise

    def test_delete_role_POST(self):
        uri = reverse("permafrost:role-update", kwargs={"slug": "test-role"})
        data = model_to_dict(self.pf_role)
        data.update({"deleted": True})
        ## iterator below used to remove 'description': None
        data = {k: v for k, v in data.items() if v is not None}
        self.client.post(uri, data=data, follow=True)

        try:
            updated_role = PermafrostRole.objects.get(
                slug=self.pf_role.slug, site__id=1
            )
            self.assertEqual(updated_role.deleted, True)
        except Exception as e:
            print("")
            print(
                model_to_dict(
                    PermafrostRole.objects.get(slug=self.pf_role.slug, site__id=1)
                )
            )
            print("Error: " + str(e))
            print("")
            raise

    def test_delete_locked_role_POST_returns_validation_error(self):
        self.pf_role.locked = True
        self.pf_role.save()
        uri = reverse("permafrost:role-update", kwargs={"slug": "test-role"})
        data = model_to_dict(self.pf_role)
        data.update({"deleted": True})
        ## iterator below used to remove 'description': None
        data = {k: v for k, v in data.items() if v is not None}
        self.client.post(uri, data=data, follow=True)

        try:
            updated_role = PermafrostRole.objects.get(
                slug=self.pf_role.slug, site__id=1
            )
            self.assertEqual(updated_role.deleted, False)
        except Exception as e:
            print("")
            print(
                model_to_dict(
                    PermafrostRole.objects.get(slug=self.pf_role.slug, site__id=1)
                )
            )
            print("Error: " + str(e))
            print("")
            raise

    def test_site_added_on_create_POST(self):
        site = get_current_site()
        data = {
            "name": "Test Site Role",
            "description": "Test guaranteed site added on create",
            "category": "user",
        }
        uri = reverse("permafrost:role-create")
        response = self.client.post(uri, data=data)
        try:
            role = PermafrostRole.objects.get(name="Test Site Role")
            self.assertEqual(role.site.id, site)
        except Exception as e:
            print("")
            print(response.content.decode())
            print("Error: " + str(e))
            print("")
            raise

    def test_modal_search_excludes_current_roles_REQUIRED_permissions(self):
        role = PermafrostRole.objects.get(slug="bobs-staff-group")
        uri = reverse(
            "permafrost:custom-role-add-permissions",
            kwargs={"slug": "bobs-staff-group"},
        )
        response = self.client.get(uri)

        try:
            permissions = role.required_permissions()
            for perm in permissions:
                self.assertNotContains(response, perm.name)
        except Exception as e:
            print("")
            print(response.content.decode())
            print("Error: " + str(e))
            print("")
            raise

    def test_modal_search_excludes_current_roles_SELECTED_permissions(self):
        role = PermafrostRole.objects.get(slug="bobs-staff-group")
        uri = reverse(
            "permafrost:custom-role-add-permissions",
            kwargs={"slug": "bobs-staff-group"},
        )
        response = self.client.get(uri)

        try:
            permissions = role.permissions().all()
            for perm in permissions:
                self.assertNotContains(response, perm.name)
        except Exception as e:
            print("")
            print(response.content.decode())
            print("Error: " + str(e))
            print("")
            raise

    def test_modal_POST_only_adds_permissions_allowed_for_role_category(self):
        allowed_permission = Permission.objects.get_by_natural_key(
            *("add_permafrostrole", "permafrost", "permafrostrole")
        )
        disallowed_permission = Permission.objects.get_by_natural_key(
            *("add_logentry", "admin", "logentry")
        )
        uri = reverse(
            "permafrost:custom-role-add-permissions",
            kwargs={"slug": self.pf_role.slug},
        )

        self.client.post(
            uri,
            data={
                "permissions": [
                    str(allowed_permission.id),
                    str(disallowed_permission.id),
                ]
            },
            follow=True,
        )

        role_permission_ids = set(
            self.pf_role.permissions().values_list("id", flat=True)
        )
        self.assertIn(allowed_permission.id, role_permission_ids)
        self.assertNotIn(disallowed_permission.id, role_permission_ids)

    def test_html_object_routes_do_not_mutate_foreign_context_role(self):
        foreign_role = PermafrostRole.objects.get(pk=3)
        original_permission_ids = set(
            foreign_role.permissions().values_list("id", flat=True)
        )

        scoped_routes = [
            ("get", "permafrost:role-detail", None),
            ("get", "permafrost:role-update", None),
            ("post", "permafrost:role-update", {"name": "Cross Context Rename"}),
            ("get", "permafrost:role-delete", None),
            ("post", "permafrost:role-delete", {}),
            ("get", "permafrost:custom-role-add-permissions", None),
        ]

        for method, route_name, data in scoped_routes:
            with self.subTest(method=method, route_name=route_name):
                url = reverse(route_name, kwargs={"slug": foreign_role.slug})
                response = getattr(self.client, method)(url, data=data)
                self.assertEqual(response.status_code, 404)

        modal_url = reverse(
            "permafrost:custom-role-add-permissions",
            kwargs={"slug": foreign_role.slug},
        )
        response = self.client.post(
            modal_url,
            data={"permissions": [str(self.pf_role.optional_permissions()[0].pk)]},
        )
        self.assertEqual(response.status_code, 302)

        foreign_role.refresh_from_db()
        self.assertEqual(foreign_role.name, "Administrator")
        self.assertFalse(foreign_role.deleted)
        self.assertEqual(
            set(foreign_role.permissions().values_list("id", flat=True)),
            original_permission_ids,
        )


# @tag('admin_tests')
class PermafrostFormClassTests(TestCase):
    fixtures = ["unit_test"]

    def setUp(self):
        self.create_form = PermafrostRoleCreateForm()
        self.pf_role = PermafrostRole.objects.get(slug="councilor")

    def test_create_form_first_category_choice_is_blank(self):
        self.assertEqual(
            self.create_form.fields["category"].choices[0], ("", "Choose Role Type")
        )

    def test_create_form_optional_required_permission_field_dynamic_based_initial_selected_category(
        self,
    ):
        form = PermafrostRoleCreateForm(initial={"category": "staff"})

        self.assertIn("permissions", form.fields)

        self.assertEqual(
            set(form.fields["permissions"].queryset),
            set(
                Permission.objects.filter(
                    codename__in=["add_permafrostrole", "change_permafrostrole"]
                )
            ),
        )

        form_2 = PermafrostRoleCreateForm(initial={"category": "administration"})

        self.assertEqual(
            set(form_2.fields["permissions"].queryset),
            {
                Permission.objects.get_by_natural_key(
                    *("delete_permafrostrole", "permafrost", "permafrostrole")
                )
            },
        )
        form_3 = PermafrostRoleCreateForm(initial={"category": "user"})

        self.assertEqual(
            set(form_3.fields["permissions"].queryset),
            {
                Permission.objects.get_by_natural_key(
                    *("view_permafrostrole", "permafrost", "permafrostrole")
                )
            },
        )

    def test_update_form_category_is_read_only_and_disabled(self):
        form = PermafrostRoleUpdateForm(instance=self.pf_role)
        self.assertTrue(form.fields["category"].widget.attrs["readonly"])
        self.assertTrue(form.fields["category"].disabled)

    def test_update_form_field_values_when_passed_model_instance(self):

        form = PermafrostRoleUpdateForm(instance=self.pf_role)

        self.assertEqual(form["name"].value(), self.pf_role.name)
        self.assertEqual(form["category"].value(), self.pf_role.category)
        self.assertEqual(form["description"].value(), self.pf_role.description)
        self.assertEqual(form["deleted"].value(), self.pf_role.deleted)

    def test_create_form_rejects_normalized_slug_collision(self):
        form = PermafrostRoleCreateForm(
            data={
                "name": "Councilor!",
                "description": "",
                "category": "staff",
                "permissions": [],
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_update_form_rejects_normalized_slug_collision(self):
        other_role = PermafrostRole.objects.create(
            name="Billing Team",
            category="staff",
        )
        form = PermafrostRoleUpdateForm(
            data={
                "name": "Councilor!",
                "description": other_role.description or "",
                "category": other_role.category,
                "permissions": [],
            },
            instance=other_role,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)


class PermafrostSiteMixinTests(TestCase):

    fixtures = ["unit_test"]

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create(
            username="jacob", email="jacob@…", password="top_secret"
        )

    def test_permissions_allowed_on_one_site_disabled_on_another(self):

        request = self.factory.get("/manage/")
        request.user = self.user
        request.site = Site.objects.get(pk=2)

        self.assertRaises(PermissionDenied, PermafrostRoleListView.as_view(), request)

        # add to site 2 Administrator role
        site_administrator = PermafrostRole.objects.get(pk=3)
        site_administrator.users_add(self.user)

        response = PermafrostRoleListView.as_view()(request)

        self.assertEqual(response.status_code, 200)

        # visit site 1's /manage pages
        request.site = Site.objects.get(pk=1)

        self.assertRaises(PermissionDenied, PermafrostRoleListView.as_view(), request)

    def test_multiple_roles_with_shared_permissions(self):
        """
        Both Role id 9 and 12 share a single permission: 4: view_permafrostrole
        """
        request = self.factory.get("/manage/")
        request.user = self.user
        request.site = Site.objects.get(pk=1)

        # add to site 2 Administrator role
        bobs_staff_role = PermafrostRole.objects.get(pk=4)
        bobs_staff_role.users_add(self.user)

        response = PermafrostRoleListView.as_view()(request)

        self.assertEqual(response.status_code, 200)

        councilor_staff_role = PermafrostRole.objects.get(pk=2)
        councilor_staff_role.users_add(self.user)
        response = PermafrostRoleListView.as_view()(request)

        self.assertEqual(response.status_code, 200)


class PermafrostBackendTests(TestCase):

    fixtures = ["unit_test"]

    def setUp(self):
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(
            username="context-user",
            email="context-user@example.com",
            password="top_secret",
        )
        self.site_1 = Site.objects.get(pk=1)
        self.site_2 = Site.objects.get(pk=2)
        self.permission_name = "permafrost.view_permafrostrole"
        self.site_1_role = PermafrostRole.objects.get(pk=4)
        self.site_1_role.users_add(self.user)

    def test_backend_permission_cache_does_not_leak_between_contexts(self):
        backend = PermafrostModelBackend()

        with override_settings(SITE_ID=self.site_1.pk):
            Site.objects.clear_cache()
            self.assertTrue(backend.has_perm(self.user, self.permission_name))

        with override_settings(SITE_ID=self.site_2.pk):
            Site.objects.clear_cache()
            self.assertFalse(backend.has_perm(self.user, self.permission_name))

    def test_backend_accepts_explicit_context_without_cache_leakage(self):
        backend = PermafrostModelBackend()

        self.assertIn(
            self.permission_name,
            backend.get_all_permissions(self.user, context=self.site_1),
        )
        self.assertNotIn(
            self.permission_name,
            backend.get_all_permissions(self.user, context=self.site_2),
        )

    def test_request_aware_permission_check_uses_request_context(self):
        request = self.factory.get("/")
        request.user = self.user
        request.site = self.site_1

        self.assertTrue(has_all_permissions(request, [self.permission_name]))

        request.site = self.site_2
        self.assertFalse(has_all_permissions(request, [self.permission_name]))


class PermafrostSystemCheckTests(TestCase):

    fixtures = ["unit_test"]

    @override_settings(
        AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"]
    )
    def test_global_model_backend_emits_context_scope_warning(self):
        message_ids = {
            message.id for message in check_permafrost_settings(app_configs=None)
        }

        self.assertIn("permafrost.W002", message_ids)

    @override_settings(
        AUTHENTICATION_BACKENDS=["permafrost.backends.PermafrostModelBackend"]
    )
    def test_permafrost_backend_does_not_emit_context_scope_warning(self):
        message_ids = {
            message.id for message in check_permafrost_settings(app_configs=None)
        }

        self.assertNotIn("permafrost.W002", message_ids)

    @override_settings(
        PERMAFROST_CATEGORIES={
            "broken": {
                "label": "Broken",
                "required": ["not-a-dictionary"],
                "optional": [],
            }
        }
    )
    def test_non_dictionary_permission_entry_is_reported(self):
        message_ids = {
            message.id for message in check_permafrost_settings(app_configs=None)
        }

        self.assertIn("permafrost.E008", message_ids)

    @override_settings(
        PERMAFROST_CATEGORIES={
            "broken": {
                "required": [],
                "optional": [],
            }
        }
    )
    def test_missing_category_label_is_reported(self):
        message_ids = {
            message.id for message in check_permafrost_settings(app_configs=None)
        }

        self.assertIn("permafrost.E009", message_ids)

    @override_settings(
        PERMAFROST_CATEGORIES={
            "broken": {
                "label": "Broken",
                "required": [
                    {"label": "Broken permission", "permission": ("too", "short")}
                ],
                "optional": [],
            }
        }
    )
    def test_malformed_permission_natural_key_is_reported(self):
        message_ids = {
            message.id for message in check_permafrost_settings(app_configs=None)
        }

        self.assertIn("permafrost.E010", message_ids)

    @override_settings(
        PERMAFROST_API_PAGE_SIZE=100,
        PERMAFROST_API_MAX_PAGE_SIZE=50,
    )
    def test_invalid_api_page_size_settings_are_reported(self):
        message_ids = {
            message.id for message in check_permafrost_settings(app_configs=None)
        }

        self.assertIn("permafrost.E013", message_ids)

    @override_settings(PERMAFROST_UI_PAGE_SIZE=0)
    def test_invalid_ui_page_size_setting_is_reported(self):
        message_ids = {
            message.id for message in check_permafrost_settings(app_configs=None)
        }

        self.assertIn("permafrost.E017", message_ids)

    @override_settings(PERMAFROST_API_USER_LOOKUP_FIELD="missing_field")
    def test_unknown_api_user_lookup_field_is_reported(self):
        message_ids = {
            message.id for message in check_permafrost_settings(app_configs=None)
        }

        self.assertIn("permafrost.E015", message_ids)

    @override_settings(PERMAFROST_API_USER_LOOKUP_FIELD="email")
    def test_non_unique_api_user_lookup_field_is_reported(self):
        message_ids = {
            message.id for message in check_permafrost_settings(app_configs=None)
        }

        self.assertIn("permafrost.E016", message_ids)


@override_settings(
    PERMAFROST_CONTEXT_MODEL="example.Team",
    PERMAFROST_CONTEXT_REQUEST_ATTR="team",
)
class PermafrostTeamContextTests(TestCase):

    fixtures = ["unit_test"]

    def setUp(self):
        from example.models import Team, TeamResource

        self.Team = Team
        self.TeamResource = TeamResource
        self.factory = RequestFactory()
        self.team_a = Team.objects.create(name="Team A", slug="team-a")
        self.team_b = Team.objects.create(name="Team B", slug="team-b")
        self.user = get_user_model().objects.create_user(
            username="team-user",
            email="team-user@example.com",
            password="top_secret",
        )
        self.superuser = get_user_model().objects.create_superuser(
            username="team-superuser",
            email="team-superuser@example.com",
            password="top_secret",
        )
        self.permission_name = "permafrost.view_permafrostrole"
        self.team_a_role = services.create_role(
            name="Team A Staff",
            category="staff",
            context_object=self.team_a,
        )
        self.team_b_role = services.create_role(
            name="Team B Staff",
            category="staff",
            context_object=self.team_b,
        )
        services.add_role_users(self.team_a_role, [self.user])

    def request_for(self, team, user=None):
        request = self.factory.get("/permafrost/")
        request.user = user or self.user
        request.team = team
        return request

    def test_team_roles_do_not_require_placeholder_site(self):
        self.assertIsNone(self.team_a_role.site_id)
        self.assertEqual(self.team_a_role.context, self.team_a)
        self.assertEqual(self.team_b_role.context, self.team_b)

    def test_role_form_creates_team_role_without_placeholder_site(self):
        form = PermafrostRoleCreateForm(
            data={
                "name": "Team Form Role",
                "description": "",
                "category": "staff",
                "permissions": [],
            },
            context_object=self.team_a,
        )

        self.assertTrue(form.is_valid(), form.errors)
        role = form.save()
        self.assertEqual(role.context, self.team_a)
        self.assertIsNone(role.site_id)

    def test_request_permission_is_limited_to_active_team(self):
        self.assertTrue(
            has_all_permissions(
                self.request_for(self.team_a),
                [self.permission_name],
            )
        )
        self.assertFalse(
            has_all_permissions(
                self.request_for(self.team_b),
                [self.permission_name],
            )
        )

    def test_html_view_permission_and_queryset_are_limited_to_active_team(self):
        response = PermafrostRoleListView.as_view()(self.request_for(self.team_a))

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.team_a_role, response.context_data["object_list"])
        self.assertNotIn(self.team_b_role, response.context_data["object_list"])

        with self.assertRaises(PermissionDenied):
            PermafrostRoleListView.as_view()(self.request_for(self.team_b))

    @skipIf(SKIP_DRF_TESTS, "Django Rest Framework not installed, skipping tests")
    def test_http_api_permission_and_queryset_are_limited_to_active_team(self):
        from rest_framework.test import APIRequestFactory, force_authenticate

        from .api.views import PermafrostRoleViewSet

        view = PermafrostRoleViewSet.as_view({"get": "list"})
        request = APIRequestFactory().get("/api/permafrost/v1/roles/")
        request.team = self.team_a
        force_authenticate(request, user=self.user)

        response = view(request)
        returned_slugs = {role["slug"] for role in response.data["results"]}

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.team_a_role.slug, returned_slugs)
        self.assertNotIn(self.team_b_role.slug, returned_slugs)

        request = APIRequestFactory().get("/api/permafrost/v1/roles/")
        request.team = self.team_b
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, 403)

    def test_service_default_context_uses_team_manager(self):
        with override_settings(CURRENT_TEAM_ID=self.team_a.pk):
            roles = services.list_roles()

        self.assertIn(self.team_a_role, roles)
        self.assertNotIn(self.team_b_role, roles)

    def test_business_objects_must_be_filtered_by_request_team(self):
        resource_a = self.TeamResource.objects.create(
            team=self.team_a,
            name="Team A Resource",
        )
        resource_b = self.TeamResource.objects.create(
            team=self.team_b,
            name="Team B Resource",
        )
        request = self.request_for(self.team_a)
        resources = self.TeamResource.objects.filter(team=request.team)

        self.assertIn(resource_a, resources)
        self.assertNotIn(resource_b, resources)

    def test_wrong_context_model_is_rejected(self):
        request = self.request_for(Site.objects.get(pk=1))

        with self.assertRaises(ImproperlyConfigured):
            has_all_permissions(request, [self.permission_name])

        with self.assertRaises(ImproperlyConfigured):
            services.create_role(
                name="Wrong Context",
                category="staff",
                context_object=Site.objects.get(pk=1),
            )

    def test_deleting_team_deletes_its_roles_and_groups_only(self):
        team_a_role_id = self.team_a_role.pk
        team_a_group_id = self.team_a_role.group_id
        team_b_role_id = self.team_b_role.pk

        self.team_a.delete()

        self.assertFalse(PermafrostRole.objects.filter(pk=team_a_role_id).exists())
        self.assertFalse(Group.objects.filter(pk=team_a_group_id).exists())
        self.assertTrue(PermafrostRole.objects.filter(pk=team_b_role_id).exists())

    def test_superuser_has_all_permissions_in_every_team(self):
        team_a_request = self.request_for(self.team_a, user=self.superuser)
        team_b_request = self.request_for(self.team_b, user=self.superuser)

        self.assertTrue(has_all_permissions(team_a_request, [self.permission_name]))
        self.assertTrue(has_all_permissions(team_b_request, [self.permission_name]))

        backend = PermafrostModelBackend()
        self.assertIn(
            self.permission_name,
            backend.get_all_permissions(self.superuser, context=self.team_a),
        )
        self.assertIn(
            self.permission_name,
            backend.get_all_permissions(self.superuser, context=self.team_b),
        )
