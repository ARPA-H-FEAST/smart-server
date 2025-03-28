from django.urls import path

from . import views

urlpatterns = [
    path("ping/", views.ping, name="ping"),
    path("search/", views.search, name="search"),
    path("fhir-metadata/", views.fhir_metadata, name="fhir-metadata"),
    path("fhir-openapi/", views.fhir_openapi, name="fhir-openapi"),
    path("endpoints/", views.get_fhir_endpoints, name="fhir-api-endpoints"),
    # path("dataset/search/", views.check_login_and_get_files, name="dataset-search"),
    # path("fhir-metadata/", views.fhir_metadata, name="fhir-metadata"),
    # path("fhir-openapi/", views.fhir_openapi, name="fhir-openapi"),
    path("fhir-query/", views.query_fhir, name="fhir-queries"),
]
