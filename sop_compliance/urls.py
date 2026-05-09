"""
URL patterns for NetBox SopCompliance Plugin.

For more information on URL routing, see:
https://docs.netbox.dev/en/stable/plugins/development/views/#url-registration

For Django URL patterns, see:
https://docs.djangoproject.com/en/stable/topics/http/urls/
"""

from django.urls import path
from netbox.views.generic import ObjectChangeLogView

from . import models, views

urlpatterns = (
    path("sopcompliances/", views.SopcomplianceListView.as_view(), name="sopcompliance_list"),
    path("sopcompliances/add/", views.SopcomplianceEditView.as_view(), name="sopcompliance_add"),
    path("sopcompliances/<int:pk>/", views.SopcomplianceView.as_view(), name="sopcompliance"),
    path("sopcompliances/<int:pk>/edit/", views.SopcomplianceEditView.as_view(), name="sopcompliance_edit"),
    path("sopcompliances/<int:pk>/delete/", views.SopcomplianceDeleteView.as_view(), name="sopcompliance_delete"),
    path(
        "sopcompliances/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="sopcompliance_changelog",
        kwargs={"model": models.Sopcompliance},
    ),
)
