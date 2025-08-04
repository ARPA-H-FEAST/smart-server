from drf_yasg import openapi

def get_file_detail_config():
    return {
    "200": openapi.Response(
        description="Success",
        examples={
            "application/json": {
                "headers": {
                    "Content-Type": "application/json",
                    "X-CSRFToken": "[token]"
                    },
                "bcoid": "FEAST_000012",
            }
        }
    ),
}
def get_file_detail_parameters():
    return [
        openapi.Parameter(
            "bcoid", in_=openapi.IN_BODY, type=openapi.TYPE_STRING,
            
        ),
    ]