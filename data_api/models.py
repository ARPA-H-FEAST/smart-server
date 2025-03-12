from django.db import models
from django.core.files.storage import FileSystemStorage
from django.conf import settings

# fs_api = FileSystemStorage(settings.DATA_HOME)

from pathlib import Path

RELEASED_DATA_PATH = settings.DATA_HOME / Path("releases/current/")

BCO_PATH = RELEASED_DATA_PATH / "jsondb/bcodb"
TAR_PATH = RELEASED_DATA_PATH / "tarballs/"


# Create your models here.
class BCOFileDescriptor(models.Model):
    bcoid = models.CharField(max_length=255)
    bco_file_path = models.FilePathField(path=BCO_PATH)
    keywords = models.JSONField(null=False, default=list)  # description_domain/keywords
    body_sites = models.JSONField(
        null=True, default=list
    )  # extension_domain/body_sites
    access_categories = models.JSONField(
        null=True, default=list
    )  # extension_domain/dataset_categories
    files_represented = models.JSONField(null=True, default=list)
    tar_path = models.FilePathField(path=TAR_PATH)
