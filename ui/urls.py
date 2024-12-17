from django.urls import path

from . import views

urlpatterns = [
    path("ping/", views.ping, name="ping"),
    path("search/", views.search, name="search"),
    path("fhir-metadata/", views.fhir_metadata, name="fhir-metadata"),
    path("fhir-openapi/", views.fhir_openapi, name="fhir-openapi"),
    path("query/", views.query_fhir, name="fhir-queries"),
]
