from django.db import models
from django.core.files.storage import FileSystemStorage
from django.conf import settings

# fs_api = FileSystemStorage(settings.DATA_HOME)

from pathlib import Path

# Create your models here.
class BCOFileDescriptor(models.Model):
    bcoid = models.CharField(max_length=255)
    keywords = models.JSONField(null=False, default=list)  # description_domain/keywords
    body_sites = models.JSONField(
        null=True, default=list
    )  # extension_domain/body_sites
    access_categories = models.JSONField(
        null=True, default=list
    )  # extension_domain/dataset_categories
    files_represented = models.JSONField(null=True, default=list)
    usability_domain = models.CharField(max_length=500, default="No description provided")
