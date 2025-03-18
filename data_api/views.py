from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse

from wsgiref.util import FileWrapper

from .models import BCOFileDescriptor
from .serializers import BCOandFileSerializer

import json
import logging
import os

# Create your views here.

logger = logging.getLogger()

DATA_HOME = settings.DATA_HOME
BCO_HOME = DATA_HOME / "jsondb/bcodb/"
TARBALL_FILE_HOME = DATA_HOME / "tarballs/"


@login_required
def get_available_files(request):
    method = request.method
    user = request.user

    logger.debug(f"---> Found method {method}  :: User {request.user}")
    files_available = BCOFileDescriptor.objects.all()
    file_list = [BCOandFileSerializer(f).data for f in files_available]

    # logger.debug(f"---> Found files {file_list}")

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

    bco_model = BCOFileDescriptor.objects.get(bcoid=bcoid)
    logger.debug(f"Found BCO data: {BCOandFileSerializer(bco_model).data}")

    logger.debug(f"---> Searching directory {BCO_HOME} for file {bcoid}.json")

    with open(os.path.join(BCO_HOME, f"{bcoid}.json"), "r") as fp:
        bco = json.load(fp)

    response = {
        "bco": bco,
        "fileobjlist": [{"filename": f} for f in bco_model.files_represented],
    }

    return JsonResponse(response, safe=False)


@login_required
def download(request):
    user = request.user
    file_info = json.loads(request.body)

    logger.debug(f"---> Download: Found request info {file_info}")

    if settings.DJANGO_MODE == "dev":

        file_name = file_info["filename"]
        file_path = TARBALL_FILE_HOME / f"{file_name}"

        logger.debug(f"DEV SERVER: Attempting to serve {file_name}")

        if not os.path.isfile(file_path):
            return JsonResponse(
                {"error": f"File {file_name} not found"}, status=404, safe=False
            )

        try:
            return FileResponse(open(file_path, "rb"), filename=file_name)
        except Exception as e:
            logger.debug(f"---->>>> EXCEPTION: {e}")
