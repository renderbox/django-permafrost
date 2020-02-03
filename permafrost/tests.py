import json

from django.test import TestCase, RequestFactory, Client
from django.contrib.auth import get_user_model
from django.views.generic import TemplateView
from django.urls import reverse, reverse_lazy
from django.contrib.sites.models import Site

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from headless.models import Collection
from inventory import views
from inventory.models import Step, StepRevision, Path, PathRevision, PathStep
from core import views
from core.tests import DataTestMixin
from core.models import Role, TrainingCampUser, RoleAssignment
from catalog.models import Catalog, Offering
from perms.views import PermCheckMixin


# class PermTestView(PermCheckMixin, TemplateView):
#     template_name = "core/index.html"



# # Create your tests here.
# class PermTestUser(TestCase):

#     fixtures = ['unit_test']

#     def setUp(self):
#         self.superuser = get_user_model().objects.get(pk=6)
#         self.user = get_user_model().objects.get(pk=2)
#         self.staffuser = get_user_model().objects.get(pk=3)
#         self.factory = RequestFactory()

#     def get_view(self, mode, perms, perms_get=[], perms_post=[]):
#         PermTestView.perms = perms   # Set the required perms for the test
#         PermTestView.perms_get = perms_get
#         PermTestView.mode = mode

#         return PermTestView

#     def get_request(self, resource, user):
#         request = self.factory.get(resource)
#         request.user = user
#         return request

#     def test_user_perms(self):
#         '''
#         Confirm the perms for each user type
#         '''
#         perms = {
#             'create-step', 'edit-step',
#             'delete-step', 'create-path',
#             'edit-path', 'delete-path',
#             'create-connection', 'edit-connection',
#             'delete-connection', 'create-catalog',
#             'delete-catalog', 'retrieve-message',
#             'retrieve-connection', 'retrieve-step',
#             'retrieve-path', 'view-announcement',
#             'create-message', 'edit-catalog',
#             'retrieve-catalog', 'delete-message',
#             'create-new-user', 'edit-announcement',
#             'delete-role', 'update-admin-announcement',
#             'view-user', 'create-announcement',
#             'edit-site-configuration', 'create-admin-announcement',
#             'delete-admin-announcement', 'update-role',
#             'view-admin-announcement-list', 'view-role-list',
#             'update-user-information', 'delete-user',
#             'assign-role-to-user', 'delete-announcement',
#             'create-role', 'admin-path-delete',
#             'view-admin-path-list', 'admin-deenroll',
#             'view-admin-dashboard', 'admin-enroll',
#             'path-rev-remove-step', 'path-rev-add-step',
#             'retrieve-editable-steps', 'path-rev-steps',
#             'retrieve-rating', 'publish-path-revision',
#             'view-step-rev'
#         }

#         staff_perms = {
#             'delete-message', 'view-announcement',
#             'retrieve-step', 'retrieve-message',
#             'retrieve-connection', 'retrieve-path',
#             'create-announcement', 'edit-announcement',
#             'create-message', 'retrieve-progression',
#             'retrieve-catalog', 'retrieve-grade',
#             'delete-announcement', 'update-progression',
#             'update-grade', 'view-student-record',
#             'path-rev-steps', 'retrieve-rating',
#             'view-step-rev', 'instructor-homework-retrieve'
#         }

#         user_perms = {
#             'view-student-record', 'retrieve-path',
#             'view-announcement', 'retrieve-step',
#             'retrieve-grade', 'retrieve-message',
#             'retrieve-connection', 'retrieve-catalog',
#             'retrieve-progression', 'create-message',
#             'update-rating', 'retrieve-rating',
#             'path-rev-steps', 'homework-retrieve',
#             'homework-submit', 'view-step-rev'
#         }

#         self.assertEqual(self.superuser.perms(), perms) # User with All Perms
#         self.assertEqual(self.staffuser.perms(), staff_perms)
#         self.assertEqual(self.user.perms(), user_perms)

#     def test_superuser_has_perms(self):
#         '''
#         Test that a user with
#         '''
#         View = self.get_view("any", ['edit-step', 'edit-path'])
#         request = self.get_request('/', self.superuser)

#         response = View.as_view()(request)
#         self.assertEqual(response.status_code, 200)

#     def test_user_does_not_have_permission(self):

#         View = self.get_view("any", ['edit-step', 'edit-path'])
#         request = self.get_request('/', self.user)

#         response = View.as_view()(request)
#         self.assertEqual(response.status_code, 403)

#     def test_user_has_permission(self):

#         View = self.get_view("any", [])
#         request = self.get_request('/', self.user)

#         self.assertEqual(View.get_perms(request), set() )

#         response = View.as_view()(request)
#         self.assertEqual(response.status_code, 200)

#     def test_superuser_still_has_permission(self):

#         View = self.get_view("any", [])
#         request = self.get_request('/', self.superuser)

#         response = View.as_view()(request)
#         self.assertEqual(response.status_code, 200)

#     def test_staff_user_has_permission(self):
#         '''
#         Test a case where only one permission must be met.
#         '''

#         View = self.get_view("any", ['view-student-record', 'edit-step', 'edit-path'])
#         request = self.get_request('/', self.staffuser)

#         response = View.as_view()(request)
#         self.assertEqual(response.status_code, 200)

#     def test_staff_user_needs_all_perms(self):
#         '''
#         Test a case where all perms must be met.
#         '''

#         View = self.get_view("all", ['view-student-record', 'edit-step', 'edit-path'])
#         request = self.get_request('/', self.staffuser)

#         response = View.as_view()(request)
#         self.assertEqual(response.status_code, 403)


#     def test_staff_user_has_permission(self):
#         '''
#         Test a case where only one permission must be met.
#         '''

#         View = self.get_view("any", ['edit-step', 'edit-path'], perms_get=['view-student-record'])
#         request = self.get_request('/', self.staffuser)

#         self.assertEqual(View.get_perms(request), set(['view-student-record', 'edit-step', 'edit-path']) )

#         response = View.as_view()(request)
#         self.assertEqual(response.status_code, 200)


# # ------------------------------------
# # STUDENT USER PERMISSIONS CLIENT TEST
# # ------------------------------------

# class TestStudentPermissions(DataTestMixin, TestCase):

#     fixtures = ['unit_test']

#     def setUp(self):
#         self.client = Client()
#         self.user = get_user_model().objects.get(pk=2)

#     # INVENTORY

#     def test_student_user_step_create(self):

#         uri = reverse('inventory-step-create-api')
#         self.client.force_login(self.user)

#         response = self.client.post(uri, data={'name':'Mixing 101', 'category': [1], 'effort': 5, 'summary': 'summary', 'description': 'description', 'objectives': 'objectives'})

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Return Response Code

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_student_user_step_revision_retrieve(self):

#         uri = reverse('inventory-step-detail-update-api', kwargs={'uuid': "d66f4083-4c30-48e5-9ade-c54578390391"})
#         self.client.force_login(self.user)

#         data = {
#             "name": "Testing"
#         }

#         response = self.client.get(uri)

#         try:
#             self.assertEqual(response.status_code, 200)      # 200 -> Return Response Code

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_student_user_step_revision_delete(self):

#         uri = reverse('inventory-step-revision-delete-api', kwargs={'uuid': "d66f4083-4c30-48e5-9ade-c54578390391"})
#         self.client.force_login(self.user)
#         response = self.client.delete(uri)

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Return Response Code
#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_student_user_path_create(self):

#         uri = reverse('inventory-path-create-api')
#         self.client.force_login(self.user)

#         response = self.client.post(uri, data={'name':'Mixing 101', 'category': [1]})

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Return Response Code

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_student_user_path_revision_create(self):
#         self.client.force_login(self.user)
#         path_uri = reverse('inventory-path-detail-api', kwargs={'slug': "ableton-live-5-session-view-class-1-interface-and-"})
#         path_response = self.client.get(path_uri)
#         uri = reverse('inventory-path-revision-create-api')

#         data = {
#             'name': "Revision test",
#             'step': path_response.data.get("slug"),
#             'summary': ' ',
#             'description': ' ',
#             'objectives': ' '
#         }

#         response = self.client.post(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 403)

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_student_user_path_revision_edit(self):

#         uri = reverse('inventory-path-detail-update-api', kwargs={'uuid': "1ad91f95-f260-4c4c-8ef1-57ab00afed93"})
#         self.client.force_login(self.user)

#         data = {
#             "name": "Testing"
#         }

#         response = self.client.put(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Return Response Code

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_student_user_path_revision_delete(self):
#         uri = reverse('inventory-path-revision-delete-api', kwargs={'uuid': "1ad91f95-f260-4c4c-8ef1-57ab00afed93"})
#         self.client.force_login(self.user)

#         response = self.client.delete(uri)

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Return Response Code

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_student_user_connection_create(self):
#         self.client.force_login(self.user)
#         path_uri = reverse('inventory-path-detail-update-api', kwargs={'uuid': "69bd8e82-6e03-4d02-82fb-3675d795d160"})
#         path_response = self.client.get(path_uri)
#         step_incoming_uri = reverse('inventory-step-detail-api', kwargs={'slug': "introduction-to-the-equipment"})
#         step_outgoing_uri = reverse('inventory-step-detail-api', kwargs={'slug': "introduction-to-dj"})
#         uri = reverse('inventory-connection-create-api')

#         step_incoming_response = self.client.get(step_incoming_uri)
#         step_outgoing_response = self.client.get(step_outgoing_uri)
#         data={'path':str(path_response.data.get("uuid")), 'order': 1, 'effort': 5, 'relationship': 1, 'outgoing': step_incoming_response.data.get("slug"), 'incoming': step_outgoing_response.data.get("slug")}

#         response = self.client.post(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_student_user_connection_update(self):
#         uri = reverse('inventory-connection-update-api', kwargs = {'uuid': "30d481a0-9e02-4b08-b1fc-d062234cdc67"})
#         self.client.force_login(self.user)

#         data = {
#             "order": 5
#         }

#         response = self.client.patch(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_student_user_connection_delete(self):
#         uri = reverse('inventory-connection-delete-api', kwargs = {'uuid': "30d481a0-9e02-4b08-b1fc-d062234cdc67"})
#         self.client.force_login(self.user)

#         response = self.client.delete(uri)

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     # CATALOG

#     def test_student_user_catalog_create(self):
#         uri = reverse('catalog-create-api')
#         self.client.force_login(self.user)

#         data={
#             'name':'Summer 2019'
#             }

#         response = self.client.post(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_student_user_catalog_delete(self):
#         uri = reverse('catalog-delete-api', kwargs={'slug': "summer-2019"})
#         self.client.force_login(self.user)

#         response = self.client.delete(uri)

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_student_user_offering_create(self):
#         uri = reverse('offering-create-api')
#         self.client.force_login(self.user)

#         data={
#             'catalog':'summer-2019',
#             'category': 'dj',
#             'location': 'manhattan-studio',
#             'path': 'ableton-live-5-session-view-class-1-interface-and-'
#             }

#         response = self.client.post(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response.data)
#             raise


#     def test_student_user_offering_delete(self):
#         uri = reverse('offering-delete-api', kwargs={'uuid': "41ccc38b-130a-490b-9476-d528ac6b731f"})
#         self.client.force_login(self.user)

#         response = self.client.delete(uri)

#         try:
#             self.assertEqual(response.status_code, 403)      # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response.data)
#             raise


#     # CORE-ADMIN

#         # ADMINSTRATE USERS

#     def test_student_user_retrieve_user_list(self):
#         uri = reverse('core-user-list', kwargs={'role': 'all'})
#         self.client.force_login(self.user)

#         response = self.client.get(uri)

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_student_user_create_user(self):
#         uri = reverse('core-user-create')
#         self.client.force_login(self.user)

#         data = {
#             "username": "testuser1",
#             "password": "testingpassword",
#             "email": "testuser@whitemoondreams.com"
#         }

#         response = self.client.post(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_student_user_update_user(self):
#         uri = reverse('core-user-update', kwargs={'username': 'instructor-user'})
#         self.client.force_login(self.user)

#         data = {
#             "username": "testuser"
#         }

#         response = self.client.patch(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#             # ADMINSTRATE ROLES

#     def test_student_user_retrieve_roles_list(self):
#         uri = reverse('core-role-list')
#         self.client.force_login(self.user)

#         response = self.client.get(uri)

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_student_user_delete_role(self):
#         uri = reverse('core-role-delete', kwargs={'role': 'councilor'})
#         self.client.force_login(self.user)

#         response = self.client.delete(uri)

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_student_user_edit_role(self):
#         uri = reverse('core-role-edit', kwargs={'category': 'staff', 'role': 'councilor'})
#         self.client.force_login(self.user)

#         data = {
#             "name": "councilor-role"
#         }

#         response = self.client.post(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_student_user_assign_role(self):
#         uri = reverse('core-role-assign')
#         self.client.force_login(self.user)

#         role = Role.objects.get(pk=1)
#         site = Site.objects.get(pk=4)

#         data = {
#             "role": role.slug,
#             "user": self.user.username,
#             "site": site.domain
#         }

#         response = self.client.post(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#             # ADMINSTRATE ANNOUNCEMENT

#     def test_student_user_annoucenement_update(self):
#         uri = reverse('admin-announcement-update', kwargs={'uuid': "6f89dff4-7cb9-40e8-9c7a-0e258bda1ce0"})
#         self.client.force_login(self.user)

#         data = {
#             "body": "Testing"
#         }


#         response = self.client.post(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_student_user_annoucenement_delete(self):
#         uri = reverse('admin-announcement-delete', kwargs={'uuid': "6f89dff4-7cb9-40e8-9c7a-0e258bda1ce0"})
#         self.client.force_login(self.user)

#         data = {
#             "deleted": True
#         }

#         response = self.client.post(uri)

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     #PROGRESSION

#     def test_student_user_grade_retrieve(self):
#         self.client.force_login(self.user)
#         uri = reverse('grade-update-api', kwargs={'pathuuid': "c46059e0-235d-4a31-a207-867e292b1948", 'username': "student-user"})
#         check_data = self.load_data('progression/validation/grade_retrieve.json')

#         response = self.client.get(uri)

#         try:
#             self.assertEqual(response.status_code, 200)     # 403 -> Return Response Code
#             self.assertEqual(response.data.keys(), check_data.keys())

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_student_user_grade_update(self):
#         self.client.force_login(self.user)
#         uri = reverse('grade-update-api', kwargs={'pathuuid': "c46059e0-235d-4a31-a207-867e292b1948", 'username': "student-user"})

#         data = {
#             "grade": 90
#         }

#         response = self.client.patch(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_student_user_progression_update(self):
#         self.client.force_login(self.user)
#         uri = reverse('progression-retrieve-api', kwargs={'pathuuid': "c46059e0-235d-4a31-a207-867e292b1948", 'stepuuid': "c354b529-b36d-4294-8d0c-04ec256e0fb2"})
#         check_data = self.load_data('progression/validation/progression_retrieve.json')


#         data = {
#             "pageuuid": "13c50a33-611a-4c8f-9ad8-22bf3de0c549",
#             "percentage": 70
#         }

#         response = self.client.patch(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 200)     # 200 -> Return Response Code
#             self.assertEqual(response.data.keys(), check_data.keys())


#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     #ANNOUNCEMENTS

#     def test_student_user_annoucenement_update(self):
#         self.client.force_login(self.user)
#         uri = reverse('admin-announcement-update', kwargs={'uuid': "6f89dff4-7cb9-40e8-9c7a-0e258bda1ce0"})

#         data = {
#             "body": "Testing"
#         }

#         response = self.client.patch(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden
#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_student_user_annoucenement_delete(self):
#         self.client.force_login(self.user)
#         uri = reverse('announcement-delete-api', kwargs={'uuid': "6f89dff4-7cb9-40e8-9c7a-0e258bda1ce0"})

#         data = {
#             "deleted": True
#         }

#         response = self.client.patch(uri)

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise



# # ------------------------------------
# # DESIGNER USER PERMISSIONS CLIENT TEST
# # ------------------------------------

# class TestDesignerPermissions(DataTestMixin, TestCase):

#     fixtures = ['unit_test']

#     def setUp(self):
#         self.client = Client()
#         self.user = get_user_model().objects.get(pk=5)
#         self.perms = self.user.perms()


#     def test_designer_permissions(self):
#         try:
#             perms = {
#                 'create-step', 'edit-step',
#                 'delete-step', 'create-path',
#                 'edit-path', 'delete-path',
#                 'create-connection', 'edit-connection',
#                 'delete-connection', 'create-catalog',
#                 'delete-catalog', 'retrieve-message',
#                 'retrieve-connection', 'retrieve-step',
#                 'retrieve-path', 'view-announcement',
#                 'create-message', 'edit-catalog',
#                 'retrieve-catalog', 'delete-message',
#                 'path-rev-remove-step', 'path-rev-add-step',
#                 'retrieve-editable-steps', 'path-rev-steps',
#                 'retrieve-rating', 'publish-path-revision',
#                 'view-step-rev'
#                 }


#             self.assertEqual(self.perms, perms)

#         except:
#             print("")
#             print(self.perms)
#             raise


#     # INVENTORY

#     def test_designer_user_step_create(self):
#         self.client.force_login(self.user)
#         uri = reverse('inventory-step-create-api')
#         check_data = self.load_data('inventory/validation/step_create.json')

#         response = self.client.post(uri, data={'name':'New Step Test', 'category': [4], 'effort': 5 })
#         content = json.loads(response.content)

#         try:
#             self.assertEqual(response.data.keys(), check_data.keys())
#             self.assertEqual(response.status_code, 201)     # 201 -> Created Response Code
#             self.assertNotEqual(content['slug'], None)      # Confirm that there is a respons

#         except:
#             print("")
#             print(response.data)
#             raise


#     def test_designer_user_step_revision_edit(self):
#         uri = reverse('inventory-step-detail-update-api', kwargs={'uuid': "d66f4083-4c30-48e5-9ade-c54578390391"})
#         self.client.force_login(self.user)

#         data = {
#             "name": "Testing"
#         }

#         response = self.client.patch(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 200)     # 200 -> Return Response Code

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_designer_user_step_revision_delete(self):
#         uri = reverse('inventory-step-revision-delete-api', kwargs={'uuid': "d66f4083-4c30-48e5-9ade-c54578390391"})
#         self.client.force_login(self.user)
#         # step_rev_count = StepRevision.objects.all().count()
#         # response = self.client.delete(uri)
#         # step_rev_uri = reverse('inventory-step-detail-update-api', kwargs={'uuid': "d66f4083-4c30-48e5-9ade-c54578390391"})
#         # step_rev_response = self.client.get(step_rev_uri)
#         # path_step_count = PathStep.objects.all().count()
#         data = {
#             "deleted": True
#         }

#         response = self.client.patch(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 200)     # 204 -> Return Response Code
#             # self.assertEqual(step_rev_response.status_code, 404)     # 404 -> Return Response Code
#             # self.assertEqual(StepRevision.objects.all().count(), step_rev_count-1)


#         except:
#             print("")
#             print(response.data)
#             raise


#     def test_designer_user_path_create(self):
#         self.client.force_login(self.user)
#         uri = reverse('inventory-path-create-api')
#         path_count = Path.objects.all().count()
#         response = self.client.post(uri, data={'name':'Mixing 101', 'category': [1]})
#         content = json.loads(response.content)

#         try:
#             self.assertEqual(response.status_code, 201)     # 201 -> Created Response Code
#             self.assertNotEqual(content['slug'], None)      # Confirm that there is a response
#             self.assertEqual(Path.objects.all().count(), path_count+1)

#         except:
#             print("")
#             print(response.data)
#             raise


#     def test_designer_user_path_revision_edit(self):
#         self.client.force_login(self.user)
#         check_data = self.load_data('inventory/validation/path_rev_update.json')
#         path_uri = reverse('inventory-path-detail-update-api', kwargs={'uuid': "69bd8e82-6e03-4d02-82fb-3675d795d160"})
#         path_response = self.client.get(path_uri)
#         response = self.client.put(path_uri, data={'name':"Revision 1", 'summary': "summary", 'description': "description", 'objectives': "objectives" }, content_type='application/json')
#         content = json.loads(response.content)

#         try:
#             self.assertEqual(response.status_code, 200)     # 200 -> Found Response Code
#             self.assertEqual(response.data.keys(), check_data.keys())
#             self.assertEqual(response.data['attrs'].keys(), check_data['attrs'].keys())
#             self.assertNotEqual(content['uuid'], None)      # Confirm that there is a response

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response.data)
#             raise


#     def test_designer_user_path_revision_delete(self):
#         uri = reverse('inventory-path-revision-delete-api', kwargs={'uuid': "1ad91f95-f260-4c4c-8ef1-57ab00afed93"})
#         self.client.force_login(self.user)

#         # path_revision_count = PathRevision.objects.all().count()
#         # path_step_count = PathStep.objects.all().count()
#         # data = {
#         #     "deleted": True
#         # }

#         response = self.client.delete(uri)

#         # response = self.client.delete(uri)

#         try:
#             self.assertEqual(response.status_code, 200)     # 204 -> Return Response Code
#             # self.assertEqual(PathRevision.objects.all().count(), path_revision_count-1)

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_designer_user_connection_create(self):
#         self.client.force_login(self.user)
#         check_data = self.load_data('inventory/validation/connection_create.json')
#         path_uri = reverse('inventory-path-detail-update-api', kwargs={'uuid': "69bd8e82-6e03-4d02-82fb-3675d795d160"})
#         step_incoming_uri = reverse('inventory-step-detail-api', kwargs={'slug': "introduction-to-the-equipment"})
#         step_outgoing_uri = reverse('inventory-step-detail-api', kwargs={'slug': "introduction-to-dj"})
#         uri = reverse('inventory-connection-create-api')
#         path_response = self.client.get(path_uri)
#         step_incoming_response = self.client.get(step_incoming_uri)
#         step_outgoing_response = self.client.get(step_outgoing_uri)
#         path_step_count = PathStep.objects.all().count()
#         response = self.client.post(uri, data={'path':path_response.data.get("uuid"), 'order': 1, 'effort': 5, 'relationship': 1, 'outgoing': step_incoming_response.data.get("slug"), 'incoming': step_outgoing_response.data.get("slug") })
#         content = json.loads(response.content)

#         try:
#             self.assertEqual(response.data.keys(), check_data.keys())
#             self.assertEqual(response.status_code, 201)     # 201 -> Created Response Code
#             self.assertNotEqual(content['uuid'], None)      # Confirm that there is a response
#             self.assertEqual(PathStep.objects.all().count(), path_step_count+1)

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response.data)
#             raise


#     def test_designer_user_connection_update(self):
#         self.client.force_login(self.user)
#         check_data = self.load_data('inventory/validation/connection_create.json')
#         uri = reverse('inventory-connection-update-api', kwargs = {'uuid': "30d481a0-9e02-4b08-b1fc-d062234cdc67"})

#         data = {
#             "order": 5
#         }

#         response = self.client.patch(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.data.keys(), check_data.keys())
#             self.assertEqual(response.status_code, 200)     # 200 -> Return Response Code

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_designer_user_connection_delete(self):
#         self.client.force_login(self.user)
#         uri = reverse('inventory-connection-delete-api', kwargs = {'uuid': "30d481a0-9e02-4b08-b1fc-d062234cdc67"})
#         # path_step_count = PathStep.objects.all().count()

#         response = self.client.delete(uri)

#         try:
#             self.assertEqual(response.status_code, 200)     # 204 -> Return Response Code
#             # self.assertEqual(PathStep.objects.all().count(), path_step_count-1)

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     # CATALOG

#     def test_designer_user_catalog_create(self):
#         uri = reverse('catalog-create-api')
#         self.client.force_login(self.user)
#         data={'name':'Summer 2019',}
#         catalog_count = Catalog.objects.all().count()

#         response = self.client.post(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 201)     # 201 -> Return Response Code
#             self.assertEqual(Catalog.objects.all().count(), catalog_count+1)

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_designer_user_catalog_delete(self):
#         uri = reverse('catalog-delete-api', kwargs={'slug': "summer-2019"})
#         self.client.force_login(self.user)
#         catalog_count = Catalog.objects.all().count()
#         response = self.client.delete(uri)

#         try:
#             self.assertEqual(response.status_code, 204)     # 204 -> Return Response Code
#             self.assertEqual(Catalog.objects.all().count(), catalog_count-1)

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_designer_user_offering_create(self):
#         uri = reverse('offering-create-api')
#         self.client.force_login(self.user)
#         offering_count = Offering.objects.all().count()

#         data={
#             'catalog':'summer-2019',
#             'category': 'dj',
#             'location': 'manhattan-studio',
#             'path': 'ableton-live-5-session-view-class-1-interface-and-'
#             }

#         response = self.client.post(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 201)     # 201 -> Created Response Code
#             self.assertEqual(Offering.objects.all().count(), offering_count+1)

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response.data)
#             raise


#     def test_designer_user_offering_delete(self):
#         uri = reverse('offering-delete-api', kwargs={'uuid': "41ccc38b-130a-490b-9476-d528ac6b731f"})
#         self.client.force_login(self.user)
#         offering_count = Offering.objects.all().count()

#         response = self.client.delete(uri)

#         try:
#             self.assertEqual(response.status_code, 204)     # 204 -> Return Response Code
#             self.assertEqual(Offering.objects.all().count(), offering_count-1)

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response.data)
#             raise


#     # CORE-ADMIN

#         # ADMINSTRATE USERS

#     def test_designer_user_retrieve_user_list(self):
#         uri = reverse('core-user-list', kwargs={'role': 'all'})
#         self.client.force_login(self.user)

#         response = self.client.get(uri)

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_designer_user_create_user(self):
#         uri = reverse('core-user-create')
#         self.client.force_login(self.user)

#         data = {
#             "username": "testuser1",
#             "password": "testingpassword",
#             "email": "testuser@whitemoondreams.com"
#         }

#         response = self.client.post(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_designer_user_update_user(self):
#         uri = reverse('core-user-update', kwargs={'username': 'student-user'})
#         self.client.force_login(self.user)

#         data = {
#             "username": "testuser"
#         }

#         response = self.client.patch(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_designer_user_delete_user(self):
#         uri = reverse('core-user-delete', kwargs={'username': 'student-user'})
#         self.client.force_login(self.user)

#         response = self.client.delete(uri)

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#             # ADMINSTRATE ROLES

#     def test_designer_user_retrieve_roles_list(self):
#         uri = reverse('core-role-list')
#         self.client.force_login(self.user)

#         response = self.client.get(uri)

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_designer_user_delete_role(self):
#         uri = reverse('core-role-delete', kwargs={'role': 'councilor'})
#         self.client.force_login(self.user)

#         response = self.client.delete(uri)

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_designer_user_edit_role(self):
#         uri = reverse('core-role-edit', kwargs={'category':'staff','role': 'councilor'})
#         self.client.force_login(self.user)

#         data = {
#             "name": "councilor-role"
#         }

#         response = self.client.post(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_designer_user_assign_role(self):
#         uri = reverse('core-role-assign')
#         self.client.force_login(self.user)

#         role = Role.objects.get(pk=1)
#         site = Site.objects.get(pk=4)

#         data = {
#             "role": role.slug,
#             "user": self.user.username,
#             "site": site.domain
#         }

#         response = self.client.post(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#             # ADMINSTRATE ANNOUNCEMENT

#     def test_designer_user_annoucenement_update(self):
#         uri = reverse('admin-announcement-update', kwargs={'uuid': "6f89dff4-7cb9-40e8-9c7a-0e258bda1ce0"})
#         self.client.force_login(self.user)

#         data = {
#             "body": "Testing"
#         }


#         response = self.client.post(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_designer_user_annoucenement_delete(self):
#         uri = reverse('admin-announcement-delete', kwargs={'uuid': "6f89dff4-7cb9-40e8-9c7a-0e258bda1ce0"})
#         self.client.force_login(self.user)

#         data = {
#             "deleted": True
#         }

#         response = self.client.post(uri)

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise

#     #PROGRESSION

#     def test_designer_user_grade_retrieve(self):
#         self.client.force_login(self.user)
#         uri = reverse('grade-update-api', kwargs={'pathuuid': "c46059e0-235d-4a31-a207-867e292b1948", 'username': "student-user"})

#         response = self.client.get(uri)

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_designer_user_grade_update(self):
#         self.client.force_login(self.user)
#         uri = reverse('grade-update-api', kwargs={'pathuuid': "c46059e0-235d-4a31-a207-867e292b1948", 'username': "student-user"})

#         data = {
#             "grade": 90
#         }

#         response = self.client.patch(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 403)     # 403 -> Forbidden

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


# # ------------------------------------
# # ADMIN USER PERMISSIONS CLIENT TEST
# # ------------------------------------

# class TestAdminPermissions(TestCase):

#     fixtures = ['unit_test']

#     def setUp(self):
#         self.client = Client()
#         self.user = get_user_model().objects.get(pk=6)
#         self.perms = self.user.perms()


#     # ADMINSTRATE USERS

#     def test_admin_user_retrieve_user_list(self):
#         uri = reverse('core-user-list', kwargs={'role': 'all'})
#         self.client.force_login(self.user)
#         # check_data = self.load_data('perms/validation/retrieve_user_list_response.json')

#         response = self.client.get(uri)

#         try:
#             self.assertEqual(response.status_code, 200)     # 200 -> Return Response Code
#             self.assertContains(response, '<a class="text-danger" href="/admin/user/delete/student-user/">Delete</a>', status_code=200 )

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_admin_user_create_user(self):
#         self.client.force_login(self.user)
#         uri = reverse('core-user-create')

#         data = {
#             "username": "testuser1",
#             "password": "testingpassword",
#             "email": "testuser@whitemoondreams.com",
#             "repeat_password": "testingpassword",
#         }
#         user_count = TrainingCampUser.objects.count()
#         response = self.client.post(uri, data)

#         expected_uri = reverse('core-user-list', kwargs={'role': 'all'})
#         expected_response = self.client.get(expected_uri)

#         try:
#             self.assertEqual(response.status_code, 302)     # 302 -> Return Response Code
#             self.assertEqual(TrainingCampUser.objects.count(), user_count+1)
#             self.assertRedirects(response, expected_uri, status_code=302, target_status_code=200)
#             self.assertContains(expected_response, '<a class="text-danger" href="/admin/user/delete/testuser1/">Delete</a>', status_code=200 )

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_admin_user_update_user(self):
#         uri = reverse('core-user-update', kwargs={'username': 'student-user'})
#         self.client.force_login(self.user)

#         data = {
#             "username": "12testuser"
#         }

#         response = self.client.post(uri, data)

#         expected_uri = reverse('core-user-list', kwargs={'role': 'all'})
#         expected_response = self.client.get(expected_uri)

#         try:
#             self.assertEqual(response.status_code, 302)     # 302 -> Return Response Code
#             self.assertRedirects(response, expected_uri, status_code=302, target_status_code=200)
#             self.assertContains(expected_response, '<a class="text-danger" href="/admin/user/delete/12testuser/">Delete</a>', status_code=200 )

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_admin_user_delete_user(self):
#         uri = reverse('core-user-delete', kwargs={'username': 'student-user'})
#         self.client.force_login(self.user)

#         expected_uri = reverse('core-user-list', kwargs={'role': 'all'})

#         response = self.client.delete(uri)
#         expected_response = self.client.get(expected_uri)

#         user = TrainingCampUser.objects.get(username = 'student-user')

#         try:
#             self.assertEqual(response.status_code, 302)     # 302 -> Return Response Code
#             self.assertRedirects(response, expected_uri, status_code=302, target_status_code=200)
#             self.assertEqual(user.is_active, False)
#             self.assertNotContains(expected_response, '<a class="link" href="/admin/user/delete/student-user/">Delete</a>', status_code=200 )

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     # ADMINSTRATE ROLES

#     def test_admin_user_retrieve_roles_list(self):
#         uri = reverse('core-role-list')
#         self.client.force_login(self.user)

#         response = self.client.get(uri)

#         try:
#             self.assertEqual(response.status_code, 200)     # 200 -> Return Response Code
#             self.assertNotContains(response, '<a href="/admin/role/edit/curriculum-designer/">Edit</a>', status_code=200 )
#             self.assertContains(response, '<a href="/admin/role/edit/staff/councilor/">Edit Permissions</a>', status_code=200 )
          
#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_admin_user_delete_role(self):
#         uri = reverse('core-role-delete', kwargs={'role': 'councilor'})
#         self.client.force_login(self.user)

#         expected_uri = reverse('core-role-list')

#         response = self.client.delete(uri)
#         expected_response = self.client.get(expected_uri)

#         role = Role.objects.get(slug = "councilor")

#         try:
#             self.assertEqual(response.status_code, 302)     # 302 -> Return Response Code
#             self.assertRedirects(response, expected_uri, status_code=302, target_status_code=200)
#             self.assertEqual(role.deleted, True)
#             self.assertNotContains(expected_response, '<a href="/admin/role/edit/councilor/">Edit</a>', status_code=200 )
#             self.assertNotContains(expected_response, '<a href="/admin/role/edit/curriculum-designer/">Edit</a>', status_code=200 )

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise

#     def test_admin_user_retrieve_edit_form(self):
#         uri = reverse('core-role-edit', kwargs={'category':'staff','role': 'councilor'})
#         self.client.force_login(self.user)

#         response = self.client.get(uri)
#         response_to_lower = response.content.decode('utf-8').lower()
#         try:
#             self.assertEqual(response.status_code, 200) 
#             self.assertTrue("edit staff role" in response_to_lower)
#             self.assertTrue("save changes" in response_to_lower)

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response.content)
#             raise

#     def test_admin_user_retrieve_create_form(self):
#         uri = reverse('core-role-create', kwargs={'category':'user'})
#         self.client.force_login(self.user)

#         response = self.client.get(uri)
#         response_to_lower = response.content.decode('utf-8').lower()
#         try:
#             self.assertEqual(response.status_code, 200)     # 302 -> Return Response Code
#             self.assertTrue("create user role" in response_to_lower)
#             self.assertTrue("create role" in response_to_lower)

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response.content)
#             raise

#     def test_admin_user_edit_role(self):
#         uri = reverse('core-role-edit', kwargs={'category':'staff','role': 'councilor'})
#         self.client.force_login(self.user)

#         data = {
#             "name": "1councilor",
#             "category": "staff",
#             "perms": 8
#         }

#         response = self.client.post(uri, data)

#         expected_uri = reverse('core-role-list')
#         expected_response = self.client.get(expected_uri)

#         try:
#             self.assertEqual(response.status_code, 302)     # 302 -> Return Response Code
#             self.assertRedirects(response, expected_uri, status_code=302, target_status_code=200)
#             self.assertContains(expected_response, '<a href="/admin/role/edit/staff/1councilor/">Edit Permissions</a>', status_code=200 )
#             self.assertNotContains(expected_response, '<a href="/admin/role/edit/curriculum-designer/">Edit</a>', status_code=200 )

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response.content)
#             raise


#     def test_admin_user_assign_role(self):
#         uri = reverse('core-role-assign')
#         self.client.force_login(self.user)

#         data = {
#             'role': 6,
#             'user': 5
#         }

#         assignment_count = RoleAssignment.objects.count()
#         response = self.client.post(uri, data)

#         expected_uri = reverse('core-role-list')
#         expected_response = self.client.get(expected_uri)

#         try:
#             self.assertEqual(response.status_code, 302)     # 302 -> Return Response Code
#             self.assertEqual(RoleAssignment.objects.count(), assignment_count+1)
#             self.assertRedirects(response, expected_uri, status_code=302, target_status_code=200)

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response.content)
#             raise


#     # ADMINSTRATE ANNOUNCEMENTS

#     def test_admin_user_retrieve_announcement_list(self):
#         uri = reverse('admin-announcement-list')
#         self.client.force_login(self.user)

#         response = self.client.get(uri)

#         try:
#             self.assertEqual(response.status_code, 200)     # 200 -> Return Response Code
#             self.assertContains(response, '<a class="link" href="/announce/delete/announcement/admin/6f89dff4-7cb9-40e8-9c7a-0e258bda1ce0/">Delete</a>', status_code=200 )


#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response.content)
#             raise


#     def test_admin_user_annoucenement_update(self):
#         uri = reverse('admin-announcement-update', kwargs={'uuid': "6f89dff4-7cb9-40e8-9c7a-0e258bda1ce0"})
#         self.client.force_login(self.user)

#         data = {
#             "subject": "Test",
#             "body": "Testing"
#         }


#         response = self.client.post(uri, data)

#         expected_uri = reverse('admin-announcement-list')
#         expected_response = self.client.get(expected_uri)

#         try:
#             self.assertEqual(response.status_code, 302)     # 302 -> Return Response Code
#             self.assertRedirects(response, expected_uri, status_code=302, target_status_code=200)

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response.content)
#             raise


#     def test_admin_user_annoucenement_delete(self):
#         uri = reverse('admin-announcement-delete', kwargs={'uuid': "6f89dff4-7cb9-40e8-9c7a-0e258bda1ce0"})
#         self.client.force_login(self.user)

#         data = {
#             "deleted": True
#         }

#         response = self.client.post(uri, data)

#         expected_uri = reverse('admin-announcement-list')
#         expected_response = self.client.get(expected_uri)

#         try:
#             self.assertEqual(response.status_code, 302)     # 302 -> Return Response Code
#             self.assertRedirects(response, expected_uri, status_code=302, target_status_code=200)
#             self.assertNotContains(expected_response, '<a class="link" href="/announce/update/announcement/admin/6f89dff4-7cb9-40e8-9c7a-0e258bda1ce0/">Update</a>', status_code=200 )

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


# # ----------------------------------------
# # INSTRUCTOR USER PERMISSIONS CLIENT TEST
# # ----------------------------------------

# class TestInstructorPermissions(DataTestMixin, TestCase):

#     fixtures = ['unit_test']

#     def setUp(self):
#         self.client = Client()
#         self.user = get_user_model().objects.get(pk=3)
#         self.student = get_user_model().objects.get(pk=2)
#         self.perms = self.user.perms()


#     def test_instructor_permissions(self):
#         try:
#             perms =  {
#                     'delete-message', 'view-announcement',
#                     'retrieve-step', 'retrieve-message',
#                     'retrieve-connection', 'retrieve-path',
#                     'create-announcement', 'edit-announcement',
#                     'create-message', 'retrieve-progression',
#                     'retrieve-catalog', 'retrieve-grade',
#                     'delete-announcement', 'update-progression',
#                     'update-grade', 'view-student-record',
#                     'path-rev-steps', 'retrieve-rating',
#                     'view-step-rev', 'instructor-homework-retrieve'
#                     }

#             self.assertEqual(self.perms, perms)

#         except:
#             print("")
#             print(self.perms)
#             raise


#     def test_instructor_user_grade_retrieve(self):
#         self.client.force_login(self.user)
#         uri = reverse('grade-update-api', kwargs={'pathuuid': "c46059e0-235d-4a31-a207-867e292b1948", 'username': "student-user"})
#         check_data = self.load_data('progression/validation/grade_retrieve.json')


#         response = self.client.get(uri)

#         try:
#             self.assertEqual(response.status_code, 200)     # 403 -> Return Response Code
#             self.assertEqual(response.data.keys(), check_data.keys())

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_instructor_user_grade_update(self):
#         self.client.force_login(self.user)
#         uri = reverse('grade-update-api', kwargs={'pathuuid': "c46059e0-235d-4a31-a207-867e292b1948", 'username': "student-user"})
#         check_data = self.load_data('progression/validation/grade_retrieve.json')

#         data = {
#             "grade": 90
#         }

#         response = self.client.patch(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 200)     # 200 -> Return Response Code
#             self.assertEqual(response.data.keys(), check_data.keys())


#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response)
#             raise


#     def test_instructor_user_annoucenement_update(self):
#         self.client.force_login(self.user)
#         uri = reverse('announcement-update-api', kwargs={'uuid': "6f89dff4-7cb9-40e8-9c7a-0e258bda1ce0"})
#         check_data = self.load_data('announce/validation/announce_update_response.json')


#         data = {
#             "body": "Testing"
#         }

#         response = self.client.patch(uri, data=json.dumps(data), content_type='application/json')

#         try:
#             self.assertEqual(response.status_code, 200)     # 201 -> Return Response Code, OK
#             self.assertEqual(response.data.keys(), check_data.keys())

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response.data)
#             raise


#     def test_instructor_user_annoucenement_delete(self):
#         self.client.force_login(self.user)
#         uri = reverse('announcement-delete-api', kwargs={'uuid': "6f89dff4-7cb9-40e8-9c7a-0e258bda1ce0"})
#         # check_data = self.load_data('announce/validation/announce_delete_response.json')

#         # data = {
#         #     "deleted": True
#         # }

#         response = self.client.delete(uri)

#         try:
#             self.assertEqual(response.status_code, 200)     # 200 -> Return Response Code, OK
#             # self.assertEqual(response.data.keys(), check_data.keys())

#         except:     # Only print results if there is an error, but continue to raise the error for the testing tool
#             print("")
#             print(response.data)
#             raise
