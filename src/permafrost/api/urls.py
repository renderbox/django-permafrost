from django.urls import include, path

app_name = "permafrost_api"

urlpatterns = [
    path("v1/", include("permafrost.api.v1.urls")),
]
