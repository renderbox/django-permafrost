from django.urls import path

from permafrost import views

app_name = 'permafrost'

urlpatterns = [
    path("", views.PermafrostRoleListView.as_view(), name="role-list"),
    path("manage/", views.PermafrostRoleManageView.as_view(), name="roles-manage"),
    path("role/create/", views.PermafrostRoleCreateView.as_view(), name="role-create"),
    path("role/<slug:slug>/", views.PermafrostRoleDetailView.as_view(), name="role-detail"),
    path("role/<slug:slug>/update/", views.PermafrostRoleUpdateView.as_view(), name="role-update"),
    path("role/<slug:slug>/permissions/add", views.PermafrostCustomRoleDetailView.as_view(), name="custom-role-add-permissions"),
    path("role/<slug:slug>/permissions/search", views.update_permission_table, name="custom-role-search-permissions"),
]


