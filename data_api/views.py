from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required

from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse, FileResponse
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from collections import defaultdict

from .models import BCOFileDescriptor
from .serializers import BCOandFileSerializer

from .db_interfaces import DBInterface

from .adapters import (
    Patient,
    GenomicStudy,
    DiagnosticReport,
    Organization,
    convert_gwdc_to_fhir,
)

from .swagger_configs import (
    get_file_detail_config,
    get_file_detail_parameters,
)

import json
import logging
import os

# Create your views here.

logger = logging.getLogger()

DATA_HOME = settings.DATA_HOME
DB_HOME = settings.DB_HOME
BASE_DIR = settings.BASE_DIR

BCO_HOME = DATA_HOME / "jsondb/bcodb/"
TARBALL_FILE_HOME = DATA_HOME / "tarballs/"


def config_to_connections(config):
    connections = {}
    for bco_id, dataset_config in config.items():
        db_path = os.path.join(DB_HOME, dataset_config["db_location"])
        connections[bco_id] = DBInterface(db_path, dataset_config, logger)
    return connections


# Read the DB home for a configuration file, if present.
db_config_path = os.path.join(BASE_DIR, "data_api/db_interfaces/db_config.json")
if os.path.isfile(db_config_path):
    with open(db_config_path, "r") as fp:
        config = json.load(fp)
    DB_CONNECTORS = config_to_connections(config)
else:
    logger.debug(f"No DB connections defined at {db_config_path}")
    DB_CONNECTORS = {}

# @swagger_auto_schema(tags=["get_data_source"])
# methods=["get", "post"],

### TODO: Swagger UI needs (1) class views (rest_framework.views APIViews work)
### and (2) explicit calls to `post`, `get`, etc. Seems inflexible and brittle, but
### sure ...


def get_data_sources(request):

    result = {}

    for bcoid, dbi in DB_CONNECTORS.items():
        logger.debug(f"{bcoid}: Got connection to dataset {dbi.config}")
        result[bcoid] = dbi.config["dataset"]

    return JsonResponse({"results": result}, safe=False)


@csrf_exempt
def get_data_metadata_values(request):

    bcoid = json.loads(request.body)["bcoid"]

    if bcoid not in DB_CONNECTORS.keys():
        # Error handling
        return JsonResponse({"error": "failure"})

    config = DB_CONNECTORS[bcoid].config
    response = {
        "key_columns": config["key_columns"],
        "search_fields": config["search_fields"],
    }

    return JsonResponse(response, safe=False)


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


# @login_required
# @csrf_exempt
class GetFileDetail(APIView):

    @swagger_auto_schema(
        # manual_parameters=get_file_detail_parameters(),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["bcoid"],
            properties={
                "bcoid": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="BCO ID of dataset",
                    default="FEAST_000012",
                )
            },
        ),
        responses=get_file_detail_config(),
        operation_description="Get detailed information about a dataset",
    )
    def post(self, request):

        user = request.user
        params = json.loads(request.body)
        format = params.get("format", None)
        ui_required = params.get("ui_use", False)
        bcoid = params.get("bcoid", None)

        if bcoid in DB_CONNECTORS.keys():
            dbi = DB_CONNECTORS[bcoid]
            # Retrieve first N samples for display
            example_values = dbi.get_sample()
            db_metadata = dbi.get_db_metadata()
            if format == "fhir":
                ## TODO: Convert DB values to FHIR
                ## TODO: Mapping of DBs to FHIR-compliant fields
                ## e.g., the following error:
                # `Patient.__init__() got an unexpected keyword argument 'Sex'`
                for idx, sample in enumerate(example_values):
                    if idx > 0:
                        break
                    if bcoid == "FEAST_000004":
                        logger.debug(f"===> Reasoning over value\n\t{sample}")
                        converted_sample = convert_gwdc_to_fhir(sample)
                        logger.debug(f"===> Converted sample\n\t{converted_sample}")
                        fhir_sample = [Patient(converted_sample).to_json()]
                    else:
                        fhir_sample = [{}]
                example_values = fhir_sample
        else:
            example_values = None
            db_metadata = None

        if not ui_required:
            return JsonResponse(
                {
                    "db_entries": example_values,
                    "db_metadata": db_metadata,
                },
                safe=False,
            )
        logger.debug(
            f"===> Got a request for BCO information on {bcoid} from user {user}"
        )
        # logger.debug(f"Found BCO data: {BCOandFileSerializer(bco_model).data}")
        # logger.debug(f"---> Searching directory {BCO_HOME} for file {bcoid}.json")

        with open(os.path.join(BCO_HOME, f"{bcoid}.json"), "r") as fp:
            bco = json.load(fp)
        bco_model = BCOFileDescriptor.objects.get(bcoid=bcoid)

        response = {
            "bco": bco,
            "fileobjlist": [{"filename": f} for f in bco_model.files_represented],
            "db_entries": example_values,
            "db_metadata": db_metadata,
        }

        for k, v in response.items():
            logger.debug(f"Shipping {k}: {v}")

        return JsonResponse(response, safe=False)


# def get_file_detail(request):
#     user = request.user
#     params = json.loads(request.body)
#     bcoid = params.get("bcoid", None)
#     format = params.get("format", None)

#     logger.debug(f"===> Got a request for BCO information on {bcoid} from user {user}")

#     bco_model = BCOFileDescriptor.objects.get(bcoid=bcoid)
#     # logger.debug(f"Found BCO data: {BCOandFileSerializer(bco_model).data}")

#     # logger.debug(f"---> Searching directory {BCO_HOME} for file {bcoid}.json")

#     with open(os.path.join(BCO_HOME, f"{bcoid}.json"), "r") as fp:
#         bco = json.load(fp)

#     if bcoid in DB_CONNECTORS.keys():
#         dbi = DB_CONNECTORS[bcoid]
#         # Retrieve first N samples for display
#         example_values = dbi.get_sample()
#         db_metadata = dbi.get_db_metadata()
#         if format == "fhir":
#             ## TODO: Convert DB values to FHIR
#             ## TODO: Mapping of DBs to FHIR-compliant fields
#             ## e.g., the following error:
#             # `Patient.__init__() got an unexpected keyword argument 'Sex'`
#             for idx, sample in enumerate(example_values):
#                 if idx > 0:
#                     break
#                 fhir_sample = Patient(sample).to_json()
#             example_values = fhir_sample
#     else:
#         example_values = None
#         db_metadata = None

#     response = {
#         "bco": bco,
#         "fileobjlist": [{"filename": f} for f in bco_model.files_represented],
#         "db_entries": example_values,
#         "db_metadata": db_metadata
#     }

#     return JsonResponse(response, safe=False)


@login_required
def search(request):

    search_details = json.loads(request.body)
    logger.debug(f"Got search details {search_details}")
    bcoid = search_details["bcoid"]
    filters = search_details["filters"]

    logger.debug(f"Filters was {filters}")

    if filters == []:
        if bcoid in DB_CONNECTORS.keys():
            dbi = DB_CONNECTORS[bcoid]
            return JsonResponse(dbi.get_sample(), safe=False)
        else:
            return JsonResponse({}, safe=False)

    search_query = " WHERE\n\t"
    query_dict = defaultdict(list)
    for filter_entry in filters:
        column, value = filter_entry.split("|")
        query_dict[column].append(f'"{value}"')
    col_counter = 0
    for col, values in query_dict.items():
        if col_counter > 0:
            search_query += "\tAND "
        search_query += "{} IN ({})\n".format(col, ",".join(values))
        col_counter += 1

    logger.debug(f"Formed search query:\n{search_query}\n")

    if bcoid in DB_CONNECTORS.keys():
        dbi = DB_CONNECTORS[bcoid]
        example_values = dbi.get_sample(limit=None, selection_string=search_query)
    else:
        logger.error(f"Failed to find DB for {bcoid}")
        example_values = {}

    # logger.debug(f"Got DB response:\n{example_values}")

    return JsonResponse(example_values, safe=False)


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
