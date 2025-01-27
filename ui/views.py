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
import logging
import requests

logger = logging.getLogger()


# XXX - Sanity check
@csrf_exempt
def ping(request):
    logger.debug("---> MAIN APP: Received PING")
    return HttpResponse("UI/API: PONG\n")


def search(request):
    return JsonResponse({"result": "PONG"}, safe=False)


@login_required
def query_fhir(request):
    method = request.method
    query_args_string = request.GET.get("q", None)
    # logger.debug(f"Found query args {query_args_string}")
    if query_args_string is None:
        return JsonResponse({"response": "no query text provided"}, safe=False)
    match method:
        case "GET":
            fhir_response = requests.request(
                method="GET", url=f"http://localhost:8081/fhir/{query_args_string}"
            )
            response_body = fhir_response.json()
            # logger.debug(
            #     f"Got server response: {response_body}\n\n(Type {type(response_body)})"
            # )
            return JsonResponse(response_body, safe=False)
        case "POST":
            json_body = request.body.decode("utf-8")
            logger.debug(f"---> Got JSON info {json_body}")
            fhir_response = requests.request(
                headers={
                    "Content-Type": "application/json",
                },
                method="POST",
                url=f"http://localhost:8081/fhir/{query_args_string}",
                data=json_body,
            )
            response_body = fhir_response.json()
            # logger.debug(
            #     f"Got server response: {response_body}\n\n(Type {type(response_body)})"
            # )
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
