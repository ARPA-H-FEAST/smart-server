from django.urls import path

from . import views

urlpatterns = [
    path("ping/", views.ping, name="ping"),
    path("search/", views.search, name="search"),
    path("fhir/", views.query_fhir, name="fhir"),
]
