from drf_yasg import openapi


def get_dataset_detail_config():
    return {
        "200": openapi.Response(
            description="Success",
            # examples={
            #     "application/json": {
            #         "headers": {
            #             "Content-Type": "application/json",
            #             "X-CSRFToken": "[token]",
            #         },
            #         "bcoid": "FEAST_000012",
            #     }
            # },
        ),
        "400": openapi.Response(
            description="Bad request: No BCO ID given"
        )
    }

def get_dataset_metadata_config():
    return {
        "200": openapi.Response(
            description="Success",
        ),
        "400": openapi.Response(
            description="No BCO ID provided, or unknown BCO provided"
        )
    }

def get_datasets_config():
    return {
        "200": openapi.Response(
            description="Success"
        )
    }

def get_bco_config():
    return {
        "200": openapi.Response(
            description="Success",
        ),
        "400": openapi.Response(
            description="No BCO ID provided, or unknown BCO provided"
        )
    }

def get_dataset_detail_parameters():
    return [
        openapi.Parameter(
            "bcoid",
            in_=openapi.IN_BODY,
            type=openapi.TYPE_STRING,
        ),
    ]
