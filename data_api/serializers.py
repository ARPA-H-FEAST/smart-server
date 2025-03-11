from .models import BCOFileDescriptor

from rest_framework import serializers


# Serializers define the API representation.
class BCOandFileSerializer(serializers.ModelSerializer):

    class Meta:
        model = BCOFileDescriptor
        fields = [
            "bcoid",
            "file_represented",
            "keywords",
            "body_sites",
            "access_categories",
        ]
