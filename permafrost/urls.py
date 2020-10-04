from django.urls import path

from permafrost import views

app_name = 'permafrost'

urlpatterns = [
    path("roles/", views.PermafrostRoleListView.as_view(), name="role-list"),
    path("role/<slug:slug>/", views.PermafrostRoleDetailView.as_view(), name="role-detail"),
    path("role/<slug:slug>/update/", views.PermafrostRoleUpdateView.as_view(), name="role-update"),
    # path("role/add/", views.PermafrostRoleCreateView.as_view(), name="role-create"),
]


