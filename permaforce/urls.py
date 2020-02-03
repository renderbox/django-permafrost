from django.urls import path

from permafrost import views

urlpatterns = [
    path("", views.PermaforceIndexView.as_view(), name="permafrost-index"),
]
