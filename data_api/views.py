from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required

# from django.contrib.auth.mixins import ProtectedResourceView
# NB See [SO](https://stackoverflow.com/a/55224844)
# This is the class-view equivalent in DOT
from oauth2_provider.views.generic import ProtectedResourceView

# ...and this class, from [here](https://django-oauth-toolkit.readthedocs.io/en/latest/views/mixins.html),
# seems pretty clearly broken out of the box...
# import oauth2_provider.views.mixins.ClientProtectedResourceMixin as ProtectedResourceView
from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse, FileResponse
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from collections import defaultdict

from .models import BCOFileDescriptor
from .serializers import BCOandFileSerializer

from .db_interfaces import DBInterface
from .db_interfaces.cohort_db import CohortDB

from .swagger_configs import (
    get_dataset_detail_config,
    get_dataset_metadata_config,
    get_datasets_config,
    get_bco_config,
)

import json
import logging
import os
import re

from pathlib import Path

_RSID_RE = re.compile(r'^rs\d+$', re.IGNORECASE)
_COORDS_RE = re.compile(r'^(?:chr)?(\w+):(\d+):([ACGTacgt*]+):([ACGTacgt*]+)$')


def _parse_mutation_id(id_str):
    """Return {'type': 'rsid', 'rsid': ...} or {'type': 'coords', ...}, or None."""
    if _RSID_RE.match(id_str):
        return {'type': 'rsid', 'rsid': id_str}
    m = _COORDS_RE.match(id_str)
    if m:
        return {'type': 'coords', 'chrom': m.group(1),
                'pos': int(m.group(2)), 'ref': m.group(3).upper(), 'alt': m.group(4).upper()}
    return None

# Create your views here.

logger = logging.getLogger()

DATA_HOME = settings.DATA_HOME
DB_HOME = settings.DB_HOME
BASE_DIR = settings.BASE_DIR

### TODO / FIXME
BCO_HOME = DATA_HOME / "jsondb/bcodb/"
TARBALL_FILE_HOME = DATA_HOME / "tarballs/"


def config_to_connections(config):
    connections = {}
    for bco_id, dataset_config in config.items():
        # Carve-out for parquets
        db_location = dataset_config["db_location"]
        if type(db_location) is not list:
            db_path = os.path.join(DB_HOME, db_location)
        else:
            db_path = str(Path(DB_HOME).parent / db_location[1])
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

_COHORT_DB_CANDIDATES = [
    Path("/data/arpah/processed/dbgap/cohort_frequencies.duckdb"),
    BASE_DIR / "datadir/processed/dbgap/cohort_frequencies.duckdb",
]

def _init_cohort_db():
    for p in _COHORT_DB_CANDIDATES:
        if Path(p).exists():
            return CohortDB(p)
    logger.debug("Cohort frequencies DuckDB not found; run compute_cohort_frequencies.py first")
    return None

COHORT_DB = _init_cohort_db()

# @swagger_auto_schema(tags=["get_data_source"])
# methods=["get", "post"],

### TODO: Swagger UI needs (1) class views (rest_framework.views APIViews work)
### and (2) explicit calls to `post`, `get`, etc. Seems inflexible and brittle, but
### sure ...


class GetBCO(APIView):
    @swagger_auto_schema(
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
        responses=get_bco_config(),
        operation_description="Retrieve the BCO defining dataset provenance",
    )
    def post(self, request):

        bcoid = json.loads(request.body)["bcoid"]

        if not bcoid:
            return JsonResponse(
                {"error": "No BCO found in query"}, safe=False, status=400
            )

        with open(os.path.join(BCO_HOME, f"{bcoid}.json"), "r") as fp:
            bco = json.load(fp)

        return JsonResponse(bco)


# TODO: Moving to `ProtectedView` (aka, credentialling)
# breaks the response into two
class GetDataSets(ProtectedResourceView, APIView):
    @swagger_auto_schema(
        responses=get_datasets_config(),
        operation_description="Get detailed information about a dataset",
    )
    # The only "GET" in this workflow
    def get(self, request):

        result = {}

        for bcoid, dbi in DB_CONNECTORS.items():
            logger.debug(f"{bcoid}: Got connection to dataset {dbi.config}")
            result[bcoid] = dbi.config["dataset"]

        return JsonResponse({"results": result}, safe=False)


class GetDatasetMetadata(ProtectedResourceView, APIView):

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
        responses=get_dataset_metadata_config(),
        operation_description="Get detailed information about a dataset",
    )
    def post(self, request):
        bcoid = json.loads(request.body)["bcoid"]

        if not bcoid:
            return JsonResponse({"error": "No BCO ID provided"}, safe=False, status=400)

        if bcoid not in DB_CONNECTORS.keys():
            # Error handling
            return JsonResponse(
                {"error": f"Unknown BCO ID {bcoid} provided"}, safe=False, status=400
            )

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
class GetDatasetDetail(ProtectedResourceView, APIView):

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
            optional=["sample_limit", "sample_offset"],
        ),
        responses=get_dataset_detail_config(),
        operation_description="Get detailed information about a dataset",
    )
    def post(self, request):

        user = request.user
        params = json.loads(request.body)
        format = params.get("format", "fhir")
        response_shape = params.get("shape", "string")
        ui_required = params.get("ui_use", False)
        bcoid = params.get("bcoid", None)

        if bcoid is None:
            return JsonResponse(
                {"error": "No BCO ID query parameter provided"}, safe=False, status=400
            )

        if bcoid not in DB_CONNECTORS.keys():

            with open(os.path.join(BCO_HOME, f"{bcoid}.json"), "r") as fp:
                bco = json.load(fp)
            bco_model = BCOFileDescriptor.objects.get(bcoid=bcoid)

            return JsonResponse(
                {
                    "bco": bco,
                    "fileobjlist": [
                        {"filename": f} for f in bco_model.files_represented
                    ],
                }
            )

        sample_limit = params.get("sample_limit", 1)
        sample_offset = params.get("sample_offset", 0)

        dbi = DB_CONNECTORS[bcoid]
        db_metadata = dbi.get_db_metadata()

        if format == "fhir":
            ## TODO: Convert DB values to FHIR
            ## TODO: Mapping of DBs to FHIR-compliant fields
            ## e.g., the following error:
            # `Patient.__init__() got an unexpected keyword argument 'Sex'`
            entries = dbi.get_sample(
                output_format="fhir",
                data_type="patient",
                limit=sample_limit,
                offset=sample_offset,
            )
            if response_shape == "string":
                entries["data"] = entries["data"][0]
                # XXX
                # / TODO Error checking if returning a string
                #  and the sample size is > 1
            return JsonResponse(
                {
                    "db_entries": entries,
                    # "db_metadata": db_metadata,
                    "sample_start": sample_offset,
                    "sample_count": sample_limit,
                }
            )
        else:
            # Retrieve first N samples for display
            example_values = dbi.get_sample(limit=sample_limit, offset=sample_offset)

        if not ui_required:
            return JsonResponse(
                {
                    "db_entries": example_values,
                    "db_metadata": db_metadata,
                    "sample_start": sample_offset,
                    "sample_count": sample_limit,
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
            "sample_start": sample_offset,
            "sample_count": sample_offset,
        }

        # for k, v in response.items():
        #     logger.debug(f"Shipping {k}: {v}")

        return JsonResponse(response, safe=False)


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

    # search_query = " WHERE\n\t"
    query_dict = defaultdict(list)
    for filter_entry in filters:
        column, value = filter_entry.split("|")
        query_dict[column].append(f'"{value}"')
    # col_counter = 0
    # for col, values in query_dict.items():
    #     if col_counter > 0:
    #         search_query += "\tAND "
    #     search_query += "{} IN ({})\n".format(col, ",".join(values))
    #     col_counter += 1

    # logger.debug(f"Formed search query:\n{search_query}\n")

    if bcoid in DB_CONNECTORS.keys():
        dbi = DB_CONNECTORS[bcoid]
        example_values = dbi.get_sample(query_dict=query_dict)
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


class CohortStudyList(APIView):
    """List all studies with their available cohort dimensions and labels."""

    @swagger_auto_schema(
        operation_description="List all available cohort studies with their dimensions and cohort labels.",
        responses={
            "200": openapi.Response(description="Study list"),
            "503": openapi.Response(description="Cohort database not available"),
        },
    )
    def get(self, request):
        if COHORT_DB is None:
            return JsonResponse({"error": "Cohort frequency database not available"}, status=503)

        studies = {}
        for study_id, cancer_type in COHORT_DB.studies():
            dims = {}
            for dim, label in COHORT_DB.dimensions(study_id):
                dims.setdefault(dim, []).append(label)
            studies[study_id] = {"cancer_type": cancer_type, "cohort_dimensions": dims}

        return JsonResponse({"studies": studies})


class RsidCarrierView(APIView):
    """Return per-rsID carrier counts, optionally filtered by study or cancer type.

    GET ?rsids=rs12354,rs13603&cancer_type=lung&study_id=phs001273
    """

    @swagger_auto_schema(
        operation_description="Return per-rsID carrier counts across cohort studies.",
        manual_parameters=[
            openapi.Parameter(
                "rsids", openapi.IN_QUERY,
                description="Comma-separated rsID list (e.g. rs12354,rs13603). Max 100.",
                type=openapi.TYPE_STRING, required=True,
            ),
            openapi.Parameter(
                "study_id", openapi.IN_QUERY,
                description="Filter by dbGaP study ID (e.g. phs001273)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "cancer_type", openapi.IN_QUERY,
                description="Filter by cancer type abbreviation (e.g. lc, bc, pc)",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={
            "200": openapi.Response(description="Carrier counts per rsID"),
            "400": openapi.Response(description="Missing or invalid rsids parameter"),
            "503": openapi.Response(description="Cohort database not available"),
        },
    )
    def get(self, request):
        if COHORT_DB is None:
            return JsonResponse({"error": "Cohort frequency database not available"}, status=503)

        rsids_param = request.GET.get("rsids", "")
        rsids = [r.strip() for r in rsids_param.split(",") if r.strip()]
        if not rsids:
            return JsonResponse({"error": "rsids parameter required (comma-separated rsID list)"}, status=400)
        if len(rsids) > 100:
            return JsonResponse({"error": "maximum 100 rsids per request"}, status=400)

        study_id = request.GET.get("study_id") or None
        cancer_type = request.GET.get("cancer_type") or None

        variants = COHORT_DB.carrier_counts(rsids, study_id, cancer_type)
        total_patients = COHORT_DB.patient_count(study_id, cancer_type)

        return JsonResponse({
            "total_patients": total_patients,
            "study_id": study_id,
            "cancer_type": cancer_type,
            "variants": variants,
        })


class PatientListView(APIView):
    """Return per-patient SNP counts and demographics, optionally filtered by study or cancer type."""

    @swagger_auto_schema(
        operation_description="Return per-patient SNP counts and demographics.",
        manual_parameters=[
            openapi.Parameter(
                "study_id", openapi.IN_QUERY,
                description="Filter by dbGaP study ID",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "cancer_type", openapi.IN_QUERY,
                description="Filter by cancer type abbreviation",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "limit", openapi.IN_QUERY,
                description="Number of records to return (max 1000, default 100)",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "offset", openapi.IN_QUERY,
                description="Record offset for pagination",
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={
            "200": openapi.Response(description="Paginated patient list"),
            "400": openapi.Response(description="Invalid limit or offset"),
            "503": openapi.Response(description="Cohort database not available"),
        },
    )
    def get(self, request):
        if COHORT_DB is None:
            return JsonResponse({"error": "Cohort frequency database not available"}, status=503)

        study_id = request.GET.get("study_id") or None
        cancer_type = request.GET.get("cancer_type") or None

        try:
            limit = min(int(request.GET.get("limit", 100)), 1000)
            offset = int(request.GET.get("offset", 0))
        except ValueError:
            return JsonResponse({"error": "limit and offset must be integers"}, status=400)

        patients = COHORT_DB.patient_list(study_id, cancer_type, limit, offset)
        total = COHORT_DB.patient_count(study_id, cancer_type)

        return JsonResponse({
            "total": total,
            "limit": limit,
            "offset": offset,
            "patients": patients,
        })


class CohortFrequencyView(APIView):
    """Return top-N variants by alt frequency for a given study cohort."""

    @swagger_auto_schema(
        operation_description="Return top-N variants by alt frequency for a given study cohort.",
        manual_parameters=[
            openapi.Parameter(
                "dimension", openapi.IN_QUERY,
                description="Cohort dimension (e.g. stage, sex). Required.",
                type=openapi.TYPE_STRING, required=True,
            ),
            openapi.Parameter(
                "cohort", openapi.IN_QUERY,
                description="Cohort label within the dimension (e.g. III, male). Required.",
                type=openapi.TYPE_STRING, required=True,
            ),
            openapi.Parameter(
                "variant_type", openapi.IN_QUERY,
                description="Filter by variant type: snp, indel, or all (default all)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "limit", openapi.IN_QUERY,
                description="Number of top variants to return (max 100, default 20)",
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={
            "200": openapi.Response(description="Top variants with alt frequencies"),
            "400": openapi.Response(description="Missing dimension/cohort, or invalid limit"),
            "503": openapi.Response(description="Cohort database not available"),
        },
    )
    def get(self, request, cancer_type, study_id):
        if COHORT_DB is None:
            return JsonResponse({"error": "Cohort frequency database not available"}, status=503)

        cohort_dim = request.GET.get("dimension")
        cohort_label = request.GET.get("cohort")
        variant_type = request.GET.get("variant_type", "all")

        try:
            limit = min(int(request.GET.get("limit", 20)), 100)
        except ValueError:
            return JsonResponse({"error": "limit must be an integer"}, status=400)

        if not cohort_dim or not cohort_label:
            dims = {}
            for dim, label in COHORT_DB.dimensions(study_id):
                dims.setdefault(dim, []).append(label)
            return JsonResponse(
                {"error": "dimension and cohort parameters are required",
                 "available_dimensions": dims},
                status=400,
            )

        variants = COHORT_DB.top_variants(study_id, cohort_dim, cohort_label, limit, variant_type)
        sample_count = COHORT_DB.sample_count(study_id, cohort_dim, cohort_label)

        return JsonResponse({
            "study_id": study_id,
            "cancer_type": cancer_type,
            "cohort_dimension": cohort_dim,
            "cohort_label": cohort_label,
            "sample_count": sample_count,
            "variants": variants,
        })


class MutationDetailView(APIView):
    """Return variant detail (carrier counts + cohort frequencies) for a single mutation.

    Accepts rsID (rs12354) or chrom:pos:ref:alt (7:117548628:A:G).
    """

    @swagger_auto_schema(
        operation_description=(
            "Return carrier counts and per-cohort frequencies for a single mutation. "
            "ID may be an rsID (e.g. rs12354) or chrom:pos:ref:alt (e.g. 7:117548628:A:G)."
        ),
        responses={
            "200": openapi.Response(description="Mutation detail with cohort frequencies"),
            "400": openapi.Response(description="Invalid mutation ID format"),
            "404": openapi.Response(description="Mutation not found"),
            "503": openapi.Response(description="Cohort database not available"),
        },
    )
    def get(self, request, mutation_id):
        if COHORT_DB is None:
            return JsonResponse({"error": "Cohort frequency database not available"}, status=503)

        parsed = _parse_mutation_id(mutation_id)
        if not parsed:
            return JsonResponse(
                {"error": f"Invalid mutation ID '{mutation_id}'. "
                 "Use rsID (rs12354) or chrom:pos:ref:alt (7:117548628:A:G)."},
                status=400,
            )

        if parsed['type'] == 'rsid':
            variant = COHORT_DB.mutation_by_rsid(parsed['rsid'])
            cohort_freqs = COHORT_DB.mutation_cohort_freqs_by_rsid(parsed['rsid'])
        else:
            variant = COHORT_DB.mutation_by_coords(
                parsed['chrom'], parsed['pos'], parsed['ref'], parsed['alt'])
            cohort_freqs = COHORT_DB.mutation_cohort_freqs_by_coords(
                parsed['chrom'], parsed['pos'], parsed['ref'], parsed['alt'])

        if not variant:
            return JsonResponse({"error": f"Mutation not found: {mutation_id}"}, status=404)

        return JsonResponse({
            "resourceType": "Mutation",
            "id": mutation_id,
            "id_type": parsed['type'],
            "variant": variant,
            "cohort_frequencies": cohort_freqs,
        })


class MutationSearchView(APIView):
    """Search mutations by rsID list and optional cohort filters.

    POST body (JSON): {rsids, cancer_type, study_id, variant_type, limit, offset}
    """

    @swagger_auto_schema(
        operation_description="Search mutations by rsID list and optional cohort filters.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "rsids": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="List of rsIDs to search",
                ),
                "cancer_type": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Filter by cancer type abbreviation",
                ),
                "study_id": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Filter by dbGaP study ID",
                ),
                "variant_type": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Filter by variant type: snp, indel, or all",
                ),
                "limit": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Max results to return (max 100, default 20)",
                    default=20,
                ),
                "offset": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Result offset for pagination",
                    default=0,
                ),
            },
        ),
        responses={
            "200": openapi.Response(description="FHIR Bundle of matching mutations"),
            "400": openapi.Response(description="Invalid request body"),
            "503": openapi.Response(description="Cohort database not available"),
        },
    )
    def post(self, request):
        if COHORT_DB is None:
            return JsonResponse({"error": "Cohort frequency database not available"}, status=503)

        try:
            body = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON body"}, status=400)

        rsids = body.get('rsids') or []
        cancer_type = body.get('cancer_type') or None
        study_id = body.get('study_id') or None
        variant_type = body.get('variant_type') or None

        try:
            limit = min(int(body.get('limit', 20)), 100)
            offset = int(body.get('offset', 0))
        except (ValueError, TypeError):
            return JsonResponse({"error": "limit and offset must be integers"}, status=400)

        variants = COHORT_DB.mutation_search(rsids, cancer_type, study_id, variant_type, limit, offset)
        total = COHORT_DB.mutation_search_count(rsids, cancer_type, study_id, variant_type)

        return JsonResponse({
            "resourceType": "Bundle",
            "total": total,
            "limit": limit,
            "offset": offset,
            "entry": variants,
        })
