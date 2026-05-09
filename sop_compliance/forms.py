"""
Forms for NetBox SopCompliance Plugin.

For more information on NetBox forms, see:
https://docs.netbox.dev/en/stable/plugins/development/forms/
"""

from netbox.forms import NetBoxModelForm

from .models import Sopcompliance


class SopcomplianceForm(NetBoxModelForm):
    class Meta:
        model = Sopcompliance
        fields = ("name", "tags")
