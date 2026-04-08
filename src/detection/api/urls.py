"""
API URL Configuration

URL routing for the detection API endpoints.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AnalysisViewSet,
    BatchViewSet,
    DetailedHealthCheckView,
    HealthCheckView,
    ModelViewSet,
)


# Create router for viewsets
router = DefaultRouter()
# Empty prefix because this is already included under /api/v1/analysis/
router.register(r"", AnalysisViewSet, basename="analysis")
router.register(r"batch", BatchViewSet, basename="batch")
router.register(r"models", ModelViewSet, basename="models")

app_name = "detection-api"

urlpatterns = [
    # Viewset routes
    path("", include(router.urls)),
    
    # Health checks
    path("health/", HealthCheckView.as_view(), name="health"),
    path("health/detailed/", DetailedHealthCheckView.as_view(), name="health-detailed"),
]
