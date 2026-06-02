from django.urls import path, include

from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from . import views
from .views import CohortStudyList, CohortFrequencyView, PatientListView, RsidCarrierView, MutationDetailView, MutationSearchView

from django.conf import settings as django_settings

import logging
import os

logger = logging.getLogger()

_SCHEMA_URL = (
    "http://localhost:8000"
    if django_settings.DJANGO_MODE == "dev"
    else "https://feast.mgpc.biochemistry.gwu.edu"
)


# Routers provide an easy way of automatically determining the URL conf.
# router = routers.DefaultRouter()
# router.register(r"", UserViewSet)
# router.register(r"login", views.login_view)
# router.register(r"whoami", views.whoami_view)


class SchemaGenerator(OpenAPISchemaGenerator):
    # Workaround for drf-yasg basePath derivation: https://github.com/axnsan12/drf-yasg/issues/440
    def get_schema(self, request=None, public=False):
        schema = super(SchemaGenerator, self).get_schema(request, public)
        schema.basePath = "/fhir-api/data-api/"
        return schema


swagger_patterns = [
    path("dataset-detail/", views.GetDatasetDetail.as_view(), name="File detail view"),
    path("datasets/", views.GetDataSets.as_view(), name="API data source list access"),
    path(
        "dataset-metadata/",
        views.GetDatasetMetadata.as_view(),
        name="API data source metadata access",
    ),
    path("dataset-bco/", views.GetBCO.as_view(), name="BCO Access"),
    path("cohort/", CohortStudyList.as_view(), name="Cohort study list"),
    path(
        "cohort/<str:cancer_type>/<str:study_id>/snp-frequency/",
        CohortFrequencyView.as_view(),
        name="Cohort SNP frequency",
    ),
    path("patients/", PatientListView.as_view(), name="Patient list"),
    path("rsid-carriers/", RsidCarrierView.as_view(), name="rsID carrier counts"),
    path("Mutation/_search", MutationSearchView.as_view(), name="Mutation search"),
    path("Mutation/<str:mutation_id>/", MutationDetailView.as_view(), name="Mutation detail"),
]

schema_view = get_schema_view(
    openapi.Info(title="FEAST Data API", default_version="v0.1"),
    public=False,
    patterns=swagger_patterns,
    url=_SCHEMA_URL,
    urlconf="data_api.urls",
    generator_class=SchemaGenerator,
)

urlpatterns = [
    path("list/", views.get_available_files, name="Available files list"),
    path("search/", views.search, name="Access search API"),
    path("download/", views.download, name="Downloads"),
    path(
        "swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-ui"
    ),
] + swagger_patterns
