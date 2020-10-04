from django.urls import path

from permafrost import views

app_name = 'permafrost'

urlpatterns = [
    path("", views.PermafrostRoleListView.as_view(), name="role-list"),
]
