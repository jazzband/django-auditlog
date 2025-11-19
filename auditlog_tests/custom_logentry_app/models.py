from django.db import models

from auditlog.models import AbstractLogEntry


class CustomLogEntryModel(AbstractLogEntry):
    role = models.CharField(max_length=100, null=True, blank=True)
