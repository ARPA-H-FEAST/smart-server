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
    return HttpResponse("PONG\n")


def search(request):
    return JsonResponse({"result": "PONG"}, safe=False)


@login_required
def query_fhir(request):
    method = request.method
    logger.debug(f"---> Got request of method {method}")
    logger.debug(f"META keys are\n{request.META.keys()}")
    match method:
        case "GET":
            # hardcoded reponse to confirm FHIR server is there
            fhir_response = requests.request(
                method="GET", url="http://localhost:8081/fhir/metadata/"
            )
            compliance_statement = fhir_response.json()
            # logger.debug(f"Got JSON compliance string {compliance_statement}")
            return JsonResponse({"result": "confirmed"}, safe=False)
        case "POST":
            return JsonResponse({"result": "Post not yet supported"}, safe=False)
