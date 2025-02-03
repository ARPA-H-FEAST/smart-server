from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

# Create your models here.


class User(AbstractUser):

    class UserCategories(models.IntegerChoices):
        PATIENT = 1, _("Patient")
        CLINICIAN = 2, _("Clinician")
        RESEARCHER = 3, _("Researcher")
        ADMIN = 4, _("Administrator")
        BACKEND = 5, _("Backend (Automated)")

    def get_category(self):
        return self.UserCategories(self.category).label

    category = models.PositiveSmallIntegerField(
        choices=UserCategories.choices, default=UserCategories.RESEARCHER
    )
    access_groups = models.JSONField(max_length=1000, null=True)
