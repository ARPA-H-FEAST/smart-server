from django.urls import path, include


from . import views

import logging

logger = logging.getLogger()


# Routers provide an easy way of automatically determining the URL conf.
# router = routers.DefaultRouter()
# router.register(r"", UserViewSet)
# router.register(r"login", views.login_view)
# router.register(r"whoami", views.whoami_view)

urlpatterns = [
    path("search/", views.get_available_files, name="Available files list"),
    path("detail/", views.get_file_detail, name="File detail view"),
]
