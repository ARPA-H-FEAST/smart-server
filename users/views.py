import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect, csrf_exempt
from django.views.decorators.http import require_POST

from rest_framework import routers, viewsets
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser, AllowAny
from rest_framework.views import APIView

from rest_framework.renderers import JSONRenderer

from .serializers import UserSerializer
from .models import User

import logging

logger = logging.getLogger()


class CreateUser(APIView):

    def post(self, request):
        logger.debug("===> CreateUserView pinged with 'POST'")

        new_info = json.loads(request.body)
        new_info["username"] = new_info["email"]

        category = new_info.pop("category", None)

        logger.debug(f"New info:\n\n{new_info}\n\tCategory: {category}")
        # Ensure that there's no conflict of email
        previous_entry = User.objects.filter(email=new_info["email"]).first()
        logger.debug(f"==== {previous_entry} ====")
        if previous_entry:
            logger.error(
                f"=== ERROR: User email {previous_entry.email} already exists ==="
            )
            return JsonResponse(
                {"msg": f"User email {previous_entry.email} already exists"}
            )

        new_user_serializer = UserSerializer(data=new_info)
        if not new_user_serializer.is_valid():
            logger.debug("Base user information is not valid")
            logger.debug(f"+" * 40)
            logger.debug(f"{new_user_serializer.errors}")
            logger.debug(f"+" * 40)
            if "email" in new_user_serializer.errors.keys():
                return JsonResponse({"msg": new_user.errors["email"][0]}, status=401)
            for key, msg in new_user_serializer.errors.items():
                logger.debug(f"{key}: {msg}")
            return JsonResponse({"msg": "Unknown - See logs"}, status=500)
        new_user_serializer.save()
        new_user = User.objects.filter(email=new_info["email"]).first()

        new_user.set_password(new_info["password"])
        new_user.save()

        if new_user.is_superuser:
            return JsonResponse(
                {"created": new_user.get_username(), "admin": True}, status=200
            )
        return JsonResponse({"created": new_user.get_username()}, status=200)


class DeleteUser(APIView):

    def post(self, request):
        logger.debug("===> DeleteView pinged with 'POST'")
        user_key = request.data["user_id"]

        user = User.objects.filter(id=user_key)
        user.delete()

        return JsonResponse({"username": None}, status=200)

# XXX - Sanity check
@csrf_exempt
def ping(request):
    logger.debug("---> MAIN APP: Received PING")
    return HttpResponse("USERS: PONG\n")

class UpdateUser(APIView):

    def post(self, request):

        updated_info = request.data

        if not request.user.is_authenticated:
            return JsonResponse(
                {
                    "msg": "Must provide authentication credentials to perform this update",
                    "status": 0,
                }
            )

        logger.debug(f"Updating user with info:\n\n{updated_info}\n")

        user = User.objects.filter(id=updated_info["user_id"]).first()

        is_admin = request.user.is_superuser
        logger.debug(f"User: {request.user} (Is superuser? {is_admin})")

        if "new_password" in updated_info.keys():
            logger.debug("======== UPDATING PASSWORD ===========")
            if not (user.check_password(updated_info["old_password"]) or is_admin):
                return JsonResponse(
                    {"msg": "Old password is incorrect", "status": 0}, status=401
                )
            user.set_password(updated_info["new_password"])
            user.save()

            if not is_admin:
                # Allow normal users to remain logged in
                login(request, user)

        else:
            logger.debug("======== UPDATING PROFILE ===========")
            password = updated_info.pop("password")

            if not is_admin and not user.check_password(password):
                return JsonResponse({"msg": "Password is incorrect"}, status=401)
            if user.email != updated_info["email"]:
                other_users = User.objects.filter(email=updated_info["email"]).first()
                if other_users:
                    return JsonResponse(
                        {
                            "msg": f"Updated email {updated_info['email']} already exists",
                            "status": 0,
                        },
                        status=401,
                    )
            updated_info["username"] = updated_info["email"]
            user_pk = updated_info.pop("user_id")
            # Login status is not changed on "update"
            User.objects.filter(id=user_pk).update(**updated_info)

            if is_admin:
                user.set_password(password)
        if user.is_superuser:
            return JsonResponse(
                {"update": user.get_username(), "admin": True, "status": 1}, status=200
            )

        return JsonResponse({"update": user.get_username(), "status": 1}, status=200)


class UserListView(APIView):

    def get(self, request):
        logger.debug("=" * 80)
        user = request.user
        logged_in = request.user.is_authenticated

        if not logged_in:
            return JsonResponse(
                {"msg": "You must be logged in to view user information"}, status=401
            )

        # user = User.objects.filter(email=user.email).first()
        user = User.objects.filter(user=user).first()

        if not user.is_staff:
            serialized_site_info = UserSerializer(user).data
            serialized_site_info["category"] = user.get_category()
            logger.debug(f"===> Data: {serialized_site_info}")
            return JsonResponse([serialized_site_info], safe=False, status=200)

        users = User.objects.all()
        serialized_data = []
        for su in users:
            data = UserSerializer(su).data
            data["category"] = su.get_category()
            serialized_data.append(data)
        logger.debug(f"{serialized_data}")
        logger.debug("=" * 80)

        return JsonResponse(serialized_data, safe=False, status=200)


@csrf_exempt
def login_view(request):
    if request.method != "POST":
        return JsonResponse({"msg": "False"}, status=599)
    data = json.loads(request.body)
    logger.debug(f"---> Caught request! Data?: {data}")
    username = data.get("email")
    password = data.get("password")

    if username is None or password is None:
        return JsonResponse(
            {"msg": "Please provide username and password.", "status": 0}, status=400
        )

    # Failed authentication yields an HTTP 400 error code
    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse({"msg": "Invalid credentials.", "status": 0}, status=403)

    # log_info(request, user)

    logger.debug(f"Got user: {user}")

    users = User.objects.all()
    for u in users:
        logger.debug(f"DB User: {u} ---> Authenticated? {u.is_authenticated}")

    login(request, user)

    users = User.objects.all()
    for u in users:
        logger.debug(
            f"Refreshed (?) DB User: {u} ---> Authenticated? {u.is_authenticated}"
        )
    user_category = user.get_category()

    if user.is_superuser:
        response_dict = {
            "email": user.email,
            "fullname": f"{user.get_full_name()}",
            "role": user_category,
            "admin": True,
            "isAuthenticated": True,
            "status": 1,
        }
        logger.debug("V" * 80)
        logger.debug(response_dict)
        logger.debug("^" * 80)
        return JsonResponse(
            response_dict,
            status=200,
        )
    return JsonResponse(
        {
            "email": user.email,
            "fullname": f"{user.get_full_name()}",
            "role": user_category,
            "isAuthenticated": True,
            "status": 1,
        }
    )


def init(request):
    with open("./users/shims/init.json", "r") as fp:
        contents = json.load(fp)
    fp.close()
    return JsonResponse(
        {
            "status": 1,
            "record": contents,
        }
    )


def logout_view(request):
    logger.debug(f"---> Caught request! Body: {request.body}")
    logger.debug(f"---> User info? {request.user}")

    if not request.user.is_authenticated:
        return JsonResponse({"msg": "You're not logged in."}, status=400)

    logout(request)

    users = User.objects.all()

    for u in users:
        logger.debug(
            f"Refreshed (?) DB User: {u} ---> Authenticated? {u.is_authenticated}"
        )

    return JsonResponse({"msg": "Successfully logged out.", "status": 1})


def whoami_view(request):
    user = request.user

    users = User.objects.all()

    print(f"WHOAMI: Got request user {user}")
    for u in users:
        logger.debug(
            f"Refreshed (?) DB User: {u} ---> Authenticated? {u.is_authenticated}"
        )

    if not user.is_authenticated:
        return JsonResponse(
            {
                "status": 1,
                "msg": "Not authenticated",
            }
        )

    # headers = request.headers

    # XXX
    # for h in headers:
    #     logger.debug(f"===> {h}")

    users = User.objects.all()

    for u in users:
        logger.debug(
            f"Refreshed (?) DB User: {u} ---> Authenticated? {u.is_authenticated}"
        )

    if user.is_superuser:
        return JsonResponse(
            {
                "email": request.user.email,
                "fullname": f"{user.get_full_name()}",
                "role": user.category,
                "admin": True,
                "isAuthenticated": True,
                "status": 1,
            },
            status=200,
        )

    return JsonResponse(
        {
            "email": request.user.email,
            "fullname": f"{user.get_full_name()}",
            "role": user.category,
            "isAuthenticated": True,
            "status": 1,
        },
        status=200,
    )
