from django.urls import path

from permaforce import views

urlpatterns = [
    path("", views.PermaforceIndexView.as_view(), name="permaforce-index"),
]
