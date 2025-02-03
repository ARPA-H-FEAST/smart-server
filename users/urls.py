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
    path("users/", views.UserListView.as_view()),
    path("create-user/", views.CreateUser.as_view()),
    path("update-user/", views.UpdateUser.as_view()),
    path("delete-user/", views.DeleteUser.as_view()),
    path("ping/", views.ping, name="ping"),
    # XXX
    #  path("ms-oauth/authorize/", views.ms_oauth, name="3P oauth"),
    path("login/", views.login_view),
    path("logout/", views.logout_view),
    path("whoami/", views.whoami_view),
    path("init/", views.init),
    # path("api/csrf/", views.get_csrf),
    # path("api/session/", views.session_view),
    # path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
