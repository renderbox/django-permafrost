from django.urls import path

from permafrost import views

app_name = 'permafrost'

urlpatterns = [
    path("roles/", views.PermafrostRoleListView.as_view(), name="role-list"),
    path("roles/manage/", views.PermafrostRoleManageView.as_view(), name="roles-manage"),
    path("role/create/", views.PermafrostRoleCreateView.as_view(), name="role-create"),
    # path("role/<slug:slug>/", views.PermafrostRoleUpdateView.as_view(), name="role-detail"),
    path("role/<slug:slug>/update/", views.PermafrostRoleUpdateView.as_view(), name="role-update"),
]


