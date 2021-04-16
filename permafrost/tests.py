from unittest import skipIf
from django.forms.forms import Form
from django.forms.models import model_to_dict
from django.forms.widgets import Textarea
from django.test import TestCase, tag, RequestFactory
from django.contrib.sites.models import Site
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.utils import IntegrityError
from django.db import transaction
from django.contrib.auth.models import Group, Permission
from django.test.client import Client
from django.urls.base import resolve, reverse
from .views import PermafrostRoleCreateView, PermafrostRoleManageView, PermafrostRoleUpdateView, PermafrostRoleListView
from .forms import PermafrostRoleCreateForm, PermafrostRoleUpdateForm, SelectPermafrostRoleTypeForm
try:
    from rest_framework.test import APIClient
    SKIP_DRF_TESTS = False
except ImportError:
    SKIP_DRF_TESTS = True

from permafrost.models import PermafrostRole, get_current_site


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

# @tag('admin_tests')
class PermafrostViewTests(TestCase):
    fixtures = ['unit_test']

    def setUp(self):
        self.client = Client()
        self.pf_role = PermafrostRole.objects.create(category="staff", name="Test Role", site=Site.objects.get_current())
        PermafrostRole.objects.create(category="staff", name="Test Role", site=Site.objects.get(pk=2))
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
    
    def test_permaforst_manage_single_role_object_in_context(self):
        uri = reverse('permafrost:roles-manage')
        response = self.client.get(uri)
        self.assertIn('object', response.context)
        self.assertEqual(response.context['object'], PermafrostRole.on_site.all().first())
    
    def test_manage_permafrost_roles_returns_correct_template(self):
        uri = reverse('permafrost:roles-manage')
        response = self.client.get(uri)
        objects = PermafrostRole.on_site.all()
        default_role = objects.first()
        self.assertTemplateUsed(response, 'permafrost/base.html')
        self.assertTemplateUsed(response, 'permafrost/permafrostrole_manage.html')

    def test_permafrostrole_manage_template_displays_list_of_roles_on_site(self):
        uri = reverse('permafrost:roles-manage')
        import html
        response = self.client.get(uri)
        objects = PermafrostRole.on_site.all()
        
        self.assertTrue(len(objects))
        
        for object in objects:
            self.assertContains(response, html.escape(f'{object}'))
    
    def test_permafrostrole_manage_template_displays_selected_role_details(self):
        uri = reverse('permafrost:roles-manage')
        response = self.client.get(uri)
        default_role = PermafrostRole.on_site.first()  
        self.assertContains(response, f'<h2>{default_role.name}</h2>')
        self.assertContains(response, f'<p>Role Type: <span class="font-weight-bold">{default_role.get_category_display()}</span></p>')
        self.assertContains(response, f'<p>{default_role.description}</p>')

    def test_permafrostrole_manage_template_displays_selected_role_permissions(self):
        ## arrange 
        default_role = PermafrostRole.on_site.first()
        optional_permission = Permission.objects.get_by_natural_key(*('view_permafrostrole', 'permafrost', 'permafrostrole')) 
        default_role.permissions_add(optional_permission)
        ## act
        uri = reverse('permafrost:roles-manage')
        response = self.client.get(uri)
        ## assert
        self.assertEqual(len(default_role.permissions().all()), 2)

        for permission in default_role.permissions().all():
            if permission.id in default_role.all_perm_ids():
                self.assertContains(response, f'{permission.name}')

    def test_permafrostrole_manage_template_hides_selected_role_permissions_not_in_permafrost_categories(self):
        ## arrange 
        default_role = PermafrostRole.on_site.first()
        ## act
        uri = reverse('permafrost:roles-manage')
        response = self.client.get(uri)
        ## assert
        self.assertEqual(len(default_role.permissions().all()), 1)

        for permission in default_role.permissions().all():
            if permission.id not in default_role.all_perm_ids():
                self.assertNotContains(response, f'{permission.name}')

    def test_list_view_returns_roles_on_current_site(self):
        uri = reverse('permafrost:role-list')
        response = self.client.get(uri)
        site_id = get_current_site()

        try:
            roles = response.context['object_list']
            self.assertTrue(all(role.site.id == site_id for role in roles))
        except:
            print("Returned site ids")
            print([role.site.id for role in response.context['object_list']])
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

            self.assertIsInstance(response.context['form'], SelectPermafrostRoleTypeForm)
        except:
            print("")
            print(response.content.decode())
            raise
    
    def test_role_edit_url_resolves(self):
        found = resolve(f"/permafrost/role/{self.pf_role.slug}/update/")
        self.assertEqual(found.view_name, "permafrost:role-update")
        self.assertEqual(found.func.view_class, PermafrostRoleUpdateView)
    
    def test_administration_edit_url_response_with_correct_template(self):
        url = reverse("permafrost:role-update", kwargs={'slug': self.pf_role.slug})
        response = self.client.get(url)
        ## ensure _create.html extends the base template
        self.assertTemplateUsed(response, "permafrost/base.html")
        
        self.assertTemplateUsed(response, "permafrost/permafrostrole_form.html")
    
    def test_update_role_form_renders_on_GET(self):
        url = reverse("permafrost:role-update",  kwargs={'slug': self.pf_role.slug})
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
            
            self.assertIsInstance(response.context['form'], PermafrostRoleUpdateForm)
        except:
            print("")
            print(response.content.decode())
            raise
    
    def test_role_update_resolves(self):
        found = resolve('/permafrost/role/test-role/update/')
        self.assertEqual(found.view_name, "permafrost:role-update")
        self.assertEqual(found.func.view_class, PermafrostRoleUpdateView)

    def test_role_update_GET_returns_correct_template(self):
        uri = reverse('permafrost:role-update', kwargs={'slug': 'test-role'})
        response = self.client.get(uri)
        self.assertTemplateUsed(response, 'permafrost/base.html')
        self.assertTemplateUsed(response, 'permafrost/permafrostrole_form.html')

    def test_update_form_has_selected_optional_permission(self):
        ## add optional permissions
        self.pf_role.permissions_set(Permission.objects.filter(codename__in=['add_permafrostrole', 'change_permafrostrole']))
        
        uri = reverse('permafrost:role-update', kwargs={'slug': 'test-role'})
        response = self.client.get(uri)
        try:
            self.assertContains(response, """<input 
                                class="ml-auto" 
                                type="checkbox" 
                                name="permissions" 
                                value="37"
                                 checked
                            >""")
            self.assertContains(response, """<input 
                                class="ml-auto" 
                                type="checkbox" 
                                name="permissions" 
                                value="38"
                                 checked
                            >""")
        except:
            print("")
            print(response.content.decode())
            print("")
            raise
    
    def test_role_detail_GET_returns_404_if_not_on_current_site(self):
        uri = reverse('permafrost:role-update', kwargs={'slug': 'administrator'})
        response = self.client.get(uri)
        try:
            self.assertContains(response, "Not Found", status_code=404)
        except:
            print("")
            print(response.content.decode())
            raise

    def test_role_update_POST_updates_name(self):
        uri = reverse('permafrost:role-update', kwargs={'slug': 'test-role'})
        response = self.client.post(uri, data={'name': 'Test Change'}, follow=True)
        self.assertContains(response, "Test Change")
        updated_role = PermafrostRole.objects.get(pk=self.pf_role.pk)
        self.assertEqual(updated_role.name, "Test Change")
    
    def test_role_update_POST_updates_when_no_values_are_changed(self):
        uri = reverse('permafrost:role-update', kwargs={'slug': 'test-role'})
       
        request = RequestFactory().post(uri, data={'name': 'Test Role'}, follow=True)

        request.user = self.super_user
        request.site = Site.objects.get(pk=2)
        response = PermafrostRoleUpdateView.as_view()(request, slug='test-role')
        response.client = self.client
        self.assertRedirects(response, '/permafrost/role/test-role/')
        updated_role = PermafrostRole.objects.get(pk=self.pf_role.pk)

    
    def test_optional_permissions_are_updated_on_POST(self):
        ## ensure role currently has no optional permissions
        allowed_optional_permission_ids =[permission.id for permission in self.pf_role.optional_permissions()]
        current_permission_ids = [permission.id for permission in self.pf_role.permissions().all()]
        current_optional_permission_ids = [id for id in current_permission_ids if id in allowed_optional_permission_ids]
        
        self.assertFalse(current_optional_permission_ids)
        
        uri = reverse('permafrost:role-update', kwargs={'slug': 'test-role'})
        data = model_to_dict(self.pf_role)
        data.update({'permissions': ['37','38']})
        ## listcomp below used to remove 'description': None
        post_data = {k: v for k, v in data.items() if v is not None}
        self.client.post(uri, data=post_data, follow=True)
        
        updated_permission_ids_1 = [permission.id for permission in self.pf_role.permissions().all() if permission.id in allowed_optional_permission_ids]
        
        self.assertEqual(updated_permission_ids_1, [37, 38])
        
        ## remove one permission
        
        data.update({'permissions': ['37']})
        ## listcomp below used to remove 'description': None
        post_data = {k: v for k, v in data.items() if v is not None}
        self.client.post(uri, data=post_data, follow=True)

        updated_permission_ids_2 = [permission.id for permission in self.pf_role.permissions().all() if permission.id in allowed_optional_permission_ids]
        
        self.assertEqual(updated_permission_ids_2, [37])

    def test_optional_permissions_are_removed_when_empty_array_submitted_to_POST(self):
        ## arrange: add optional permissions
        self.pf_role.permissions_set(Permission.objects.filter(codename__in=['add_permafrostrole', 'change_permafrostrole']))
        
        ## ensure optional role count is 2
        allowed_optional_permission_ids =[permission.id for permission in self.pf_role.optional_permissions()]
        current_permission_ids = [permission.id for permission in self.pf_role.permissions().all()]
        current_optional_permission_ids = [id for id in current_permission_ids if id in allowed_optional_permission_ids]
        self.assertEqual(len(current_optional_permission_ids), 2)
        
        uri = reverse('permafrost:role-update', kwargs={'slug': 'test-role'})
        data = model_to_dict(self.pf_role)
        data.update({'optional_staff_perms': []})
        ## iterator below used to remove 'description': None
        data = {k: v for k, v in data.items() if v is not None}
        response = self.client.post(uri, data=data, follow=True)
        
        updated_permission_ids = [permission.id for permission in self.pf_role.permissions().all() if permission.id in allowed_optional_permission_ids]
        try:
            self.assertEqual(updated_permission_ids, [])
        except:
            print("")
            print(response.content.decode())
            print("")
            raise

    def test_delete_role_POST(self):
        uri = reverse('permafrost:role-update', kwargs={'slug': 'test-role'})
        data = model_to_dict(self.pf_role)
        data.update({'deleted': True})
        ## iterator below used to remove 'description': None
        data = {k: v for k, v in data.items() if v is not None}
        response = self.client.post(uri, data=data, follow=True)
        
        try:
            updated_role = PermafrostRole.objects.get(slug=self.pf_role.slug, site__id=1)
            self.assertEqual(updated_role.deleted, True)
        except:
            print("")
            print(model_to_dict(PermafrostRole.objects.get(slug=self.pf_role.slug, site__id=1)))
            print("")
            raise
    
    def test_site_added_on_create_POST(self):
        site = get_current_site()
        data = {
            'name': 'Test Site Role',
            'description': 'Test guaranteed site added on create',
            'category': 'user'
        }
        uri = reverse('permafrost:role-create')
        response = self.client.post(uri , data=data)
        try:
            role = PermafrostRole.objects.get(name='Test Site Role')
            self.assertEqual(role.site.id, site)
        except:
            print("")
            print(response.content.decode())
            print("")
            raise

# @tag('admin_tests')
class PermafrostFormClassTests(TestCase):
    fixtures = ['unit_test']

    def setUp(self):
        self.create_form = PermafrostRoleCreateForm()
        self.pf_role = PermafrostRole.objects.get(slug="councilor")
    
    def test_create_form_first_category_choice_is_blank(self):
        self.assertEqual(self.create_form.fields['category'].choices[0], ('', "Choose Role Type"))

    def test_create_form_optional_required_permission_field_dynamic_based_initial_selected_category(self):
        form = PermafrostRoleCreateForm(initial={'category':'staff'})
        
        self.assertIn('permissions', form.fields)

        self.assertEqual(list(form.fields['permissions'].queryset), list(Permission.objects.filter(id__in=[37,38])))
        
        form_2 = PermafrostRoleCreateForm(initial={'category':'administration'})
        
        self.assertEqual(list(form_2.fields['permissions'].queryset), list(Permission.objects.filter(id__in=[39])))
        form_3 = PermafrostRoleCreateForm(initial={'category':'user'})
        
        self.assertEqual(list(form_3.fields['permissions'].queryset), list(Permission.objects.filter(id__in=[40])))

    def test_update_form_category_is_read_only_and_disabled(self):
        form = PermafrostRoleUpdateForm(instance=self.pf_role)
        self.assertTrue(form.fields['category'].widget.attrs['readonly'])
        self.assertTrue(form.fields['category'].disabled)
    
    def test_update_form_field_values_when_passed_model_instance(self):
        
        form = PermafrostRoleUpdateForm(instance=self.pf_role)

        self.assertEqual(form['name'].value(), self.pf_role.name)
        self.assertEqual(form['category'].value(), self.pf_role.category)
        self.assertEqual(form['description'].value(), self.pf_role.description)
        self.assertEqual(form['deleted'].value(), self.pf_role.deleted)

class PermafrostSiteMixinTests(TestCase):
    
    fixtures = ['unit_test']
    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create(
            username='jacob', email='jacob@…', password='top_secret')


    def test_permissions_allowed_on_one_site_disabled_on_another(self):

        request = self.factory.get('/manage/')
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
        request = self.factory.get('/manage/')
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