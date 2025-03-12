from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import BCOFileDescriptor
from .serializers import BCOandFileSerializer

import json
import logging

# Create your views here.

logger = logging.getLogger()

DATA_HOME = settings.DATA_HOME
BCO_HOME = DATA_HOME / "releases/current/jsondb/bcodb/"
TARBALL_FILE_HOME = DATA_HOME / "releases/current/tarballs/"


@login_required
def get_available_files(request):
    method = request.method
    user = request.user

    logger.debug(f"---> Found method {method}  :: User {request.user}")
    files_available = BCOFileDescriptor.objects.all()
    file_list = [BCOandFileSerializer(f).data for f in files_available]

    logger.debug(f"---> Found files {file_list}")

    response = {
        "status": 0,
        "recordlist": file_list,
        "stats": {"total": len(file_list)},
    }

    return JsonResponse(response, safe=False)


@login_required
def get_file_detail(request):
    user = request.user
    bcoid = json.loads(request.body)["bcoid"]
    logger.debug(f"===> Got a request for BCO information on {bcoid} from user {user}")

    bco = BCOFileDescriptor.objects.get(bcoid=bcoid)
    logger.debug(f"Found BCO data: {BCOandFileSerializer(bco).data}")

    response = {
        "bco": "TBD",
        "fileobjlist": [""],
    }

    return JsonResponse(response, safe=False)
