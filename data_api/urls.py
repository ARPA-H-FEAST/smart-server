from django.urls import path, include

from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from . import views
from .views import GetFileDetail

import logging
import os

logger = logging.getLogger()


# Routers provide an easy way of automatically determining the URL conf.
# router = routers.DefaultRouter()
# router.register(r"", UserViewSet)
# router.register(r"login", views.login_view)
# router.register(r"whoami", views.whoami_view)


class SchemaGenerator(OpenAPISchemaGenerator):
    # See hacky workaround: https://github.com/axnsan12/drf-yasg/issues/440#issuecomment-520918895
    # Unclear if it has been fixed: https://github.com/axnsan12/drf-yasg/pull/682
    def get_schema(self, request=None, public=False):
        schema = super(SchemaGenerator, self).get_schema(request, public)
        schema.basePath = os.path.join(schema.basePath, "testing-ui/data-api/")
        return schema


swagger_patterns = [
    path("detail/", GetFileDetail.as_view(), name="File detail view"),
    path(
        "access/get-files/", views.get_data_sources, name="API data source list access"
    ),
    path(
        "access/ds-metadata/",
        views.get_data_metadata_values,
        name="API data source metadata access",
    ),
]

schema_view = get_schema_view(
    openapi.Info(title="FHIR Swagger Test", default_version="v0.1"),
    public=False,
    patterns=swagger_patterns,
    urlconf="data_api.urls",
    generator_class=SchemaGenerator,
)

urlpatterns = [
    path("list/", views.get_available_files, name="Available files list"),
    # path("detail/", GetFileDetail.as_view(), name="File detail view"),
    path("search/", views.search, name="Access search API"),
    path("download/", views.download, name="Downloads"),
    path(
        "swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-ui"
    ),
    # path("access/get-files/", views.get_data_sources, name="API data source list access"),
    # path("access/ds-metadata/", views.get_data_metadata_values, name="API data source metadata access"),
] + swagger_patterns
