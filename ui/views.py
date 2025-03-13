from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template.response import TemplateResponse
from django.views.decorators.csrf import (
    requires_csrf_token,
    ensure_csrf_cookie,
    csrf_exempt,
)
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core import serializers

import json
import jwt
import logging
import requests

from base64 import b64decode, b64encode

logger = logging.getLogger()


def base64URLtobase64(b64Url):
    b64Url = b64Url.replace("_", "/").replace("-", "+")
    padding = len(b64Url) % 4
    if padding > 0:
        b64Url += "=" * (4 - padding)
    return b64Url


# XXX - Sanity check
@csrf_exempt
def ping(request):
    logger.debug("---> MAIN APP: Received PING")
    return HttpResponse("UI/API: PONG\n")


with open("./fhir_schema/fhir.schema.json", "r") as fp:
    full_schema = json.load(fp)
    AVAILABLE_FHIR_ENDPOINTS = sorted(list(full_schema["definitions"].keys()))


def search(request):
    return JsonResponse({"result": "PONG"}, safe=False)


def check_login_and_get_files(request):
    method = request.method
    user = request.user

    logger.debug(f"---> Found method {method}  :: User {request.user}")

    # for name, cookie in request.COOKIES.items():
    #     logger.debug(f"COOKIE {name}: {cookie}")
    # TODO?/XXX
    # if name == "access_token_cookie":
    # encoded_secret = b64encode(b"secret")
    # encoded_signature = base64URLtobase64(cookie.split(".")[2])
    # header = cookie.split(".")[0]
    # payload = cookie.split(".")[1]
    # logger.debug(f"Headers: {b64decode(base64URLtobase64(header)).decode('utf-8')}")
    # logger.debug(f"Payload: {b64decode(base64URLtobase64(payload)).decode('utf-8')}")
    # logger.debug(f"---> Encoded signature: {encoded_signature}")
    # b64_secret = b64decode(encoded_signature)
    # new_final_segment = b64encode(b64_secret).decode('utf-8')
    # logger.debug(f"---> Decoded signature: {b64_secret} ||| New final segment: {new_final_segment}")
    # url_decoded_cookie = base64URLtobase64(cookie)
    # logger.debug(f"Decoded cookie: {url_decoded_cookie}")
    # non_encoded = header + "." + payload + "." + new_final_segment
    # XXX TODO: This JWT is *not* the OAuth workflow, but GW SSO nontheless
    # decoded = jwt.decode(non_encoded, b64_secret, algorithms=['RS256', "HS256"])
    # logger.debug("="*80)
    # logger.debug(f"Access token info: {decoded}")
    # logger.debug("="*80)
    # if name == "refresh_token_cookie":
    #     b64_secret = b64decode(cookie.split(".")[2] + "==")
    #     decoded = jwt.decode(cookie, b64_secret, algorithms=['RS256', "HS256"])
    #     logger.debug("="*80)
    #     logger.debug(f"Access token info: {decoded}")
    #     logger.debug("="*80)

    # for name, header in request.META.items():
    #     logger.debug(f"HEADER {name}: {header}")

    auth_token = request.headers.get("Authorization", None)
    logger.debug("+" * 80)
    logger.debug(f"Received auth: {auth_token}")
    logger.debug("+" * 80)

    iss_addr = json.loads(request.headers.get("Iss-Oauth", None))
    logger.debug(f"Found ISS OAuth address: {iss_addr}")

    # full_credentials = json.loads(request.headers.get("Full-Credentials", None))
    # logger.debug("+"*80)
    # for k, v in full_credentials.items():
    #     logger.debug(f"{k}: {v}")
    # logger.debug("+"*80)

    # id_token = full_credentials['id_token']
    # decoded = jwt.decode(id_token, algorithms=["HS256", "RS256"], options={"verify_signature": False})

    # logger.debug("+"*80)
    # logger.debug(f"Decoded ID:\n{decoded}")
    # logger.debug("+"*80)

    with open("./ui/shims/return_recordlist.json", "r") as fp:
        response = json.load(fp)

    return JsonResponse(response, safe=False)


def get_fhir_endpoints(request):
    return JsonResponse(AVAILABLE_FHIR_ENDPOINTS, safe=False)


@login_required
def query_fhir(request):
    method = request.method
    query_args_string = request.GET.get("q", None)
    logger.debug(f"Found query args {query_args_string}")
    if query_args_string is None:
        return JsonResponse({"response": "no query text provided"}, safe=False)
    match method:
        case "GET":
            fhir_response = requests.request(
                method="GET", url=f"http://feast-fhir-302:8081/fhir/{query_args_string}"
            )
            response_body = fhir_response.json()
            _ = response_body.pop("link", None)
            logger.debug(
                f"Got server response: {response_body}\n\n(Type {type(response_body)})"
            )
            return JsonResponse(response_body, safe=False)
        case "POST":
            json_body = request.body.decode("utf-8")
            logger.debug(f"---> Got JSON info {json_body}")
            fhir_response = requests.request(
                headers={
                    "Content-Type": "application/json",
                },
                method="POST",
                url=f"http://feast-fhir-302:8081/fhir/{query_args_string}",
                data=json_body,
            )
            _ = response_body.pop("link", None)
            response_body = fhir_response.json()
            logger.debug(
                f"Got server response: {response_body}\n\n(Type {type(response_body)})"
            )
            return JsonResponse(response_body, safe=False)
        case _:
            ...


def fhir_metadata(request):
    method = request.method
    logger.debug(f"---> Got request of method {method}")
    # logger.debug(f"META keys are\n{request.META.keys()}")
    match method:
        case "GET":
            # hardcoded reponse to confirm FHIR server is there
            fhir_response = requests.request(
                method="GET", url="http://localhost:8081/fhir/metadata/"
            )
            compliance_statement = fhir_response.json()
            # logger.debug(f"Got JSON compliance string {compliance_statement}")
            return JsonResponse(compliance_statement, safe=False)
        case "POST":
            return JsonResponse({"result": "Post not yet supported"}, safe=False)


def fhir_openapi(request):
    method = request.method
    match method:
        case "GET":
            swagger_response = requests.request(
                method="GET", url="http://localhost:8081/fhir/swagger-ui/"
            )
            return HttpResponse(swagger_response)
        case _:
            ...
