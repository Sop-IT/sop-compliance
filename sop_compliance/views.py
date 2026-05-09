"""
Views for NetBox SopCompliance Plugin.

For more information on NetBox views, see:
https://docs.netbox.dev/en/stable/plugins/development/views/

For generic view classes, see:
https://docs.netbox.dev/en/stable/development/views/
"""

from netbox.views import generic

from . import filtersets, forms, models, tables


class SopcomplianceView(generic.ObjectView):
    queryset = models.Sopcompliance.objects.all()


class SopcomplianceListView(generic.ObjectListView):
    queryset = models.Sopcompliance.objects.all()
    table = tables.SopcomplianceTable
    filterset = filtersets.SopcomplianceFilterSet


class SopcomplianceEditView(generic.ObjectEditView):
    queryset = models.Sopcompliance.objects.all()
    form = forms.SopcomplianceForm


class SopcomplianceDeleteView(generic.ObjectDeleteView):
    queryset = models.Sopcompliance.objects.all()
