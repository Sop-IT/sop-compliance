"""
Models for NetBox SopCompliance Plugin.

For more information on NetBox models, see:
https://docs.netbox.dev/en/stable/plugins/development/models/

For NetBox model features (tags, custom fields, change logging, etc.), see:
https://docs.netbox.dev/en/stable/development/models/#netbox-model-features
"""

from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel


class Sopcompliance(NetBoxModel):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        app_label = "sop_compliance"
        ordering = ("name",)
        verbose_name_plural = "Sopcompliances"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("plugins:sop_compliance:sopcompliance", args=[self.pk])
