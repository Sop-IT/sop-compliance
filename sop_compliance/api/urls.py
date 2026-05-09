"""
API URL patterns for NetBox SopCompliance Plugin.

For more information on NetBox REST API routing, see:
https://docs.netbox.dev/en/stable/plugins/development/rest-api/#routers

For Django REST Framework routers, see:
https://www.django-rest-framework.org/api-guide/routers/
"""

from netbox.api.routers import NetBoxRouter

from .views import SopcomplianceViewSet

app_name = "sop_compliance"

router = NetBoxRouter()
router.register("sopcompliances", SopcomplianceViewSet)

urlpatterns = router.urls

