from .models import User

from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = "__all__"


# Serializers define the API representation.
class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = "__all__"
