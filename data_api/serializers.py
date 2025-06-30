from .models import BCOFileDescriptor

from rest_framework import serializers


# Serializers define the API representation.
class BCOandFileSerializer(serializers.ModelSerializer):

    class Meta:
        model = BCOFileDescriptor
        fields = [
            "bcoid",
            "files_represented",
            "db_support",
            "keywords",
            "body_sites",
            "access_categories",
            "usability_domain",
        ]
