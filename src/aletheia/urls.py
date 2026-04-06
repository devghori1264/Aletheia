"""
Aletheia URL Configuration

This module defines the root URL routing for the Aletheia platform.
URLs are organized by concern:
    - /api/v1/: RESTful API endpoints
    - /admin/: Django admin interface (development only)
    - /health/: Health check endpoints
    - /: Frontend routes (served by Django or proxy)

API Versioning:
    All API endpoints are versioned under /api/v{version}/ to ensure
    backward compatibility as the API evolves.
"""

from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


def health_check(request) -> JsonResponse:
    """
    Basic health check endpoint.
    
    Returns a JSON response indicating the service is operational.
    Used by load balancers and orchestration systems.
    
    Returns:
        JsonResponse: {"status": "healthy", "service": "aletheia"}
    """
    return JsonResponse({
        "status": "healthy",
        "service": "aletheia",
        "version": "2.0.0",
    })


def ready_check(request) -> JsonResponse:
    """
    Readiness check endpoint.
    
    Verifies that the service is ready to accept traffic by checking
    critical dependencies (database, cache, etc.).
    
    Returns:
        JsonResponse: {"ready": True/False, "checks": {...}}
    """
    from django.db import connection
    
    checks = {
        "database": False,
        "cache": False,
    }
    
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = True
    except Exception:
        pass
    
    # Check cache connectivity
    try:
        from django.core.cache import cache
        cache.set("health_check", "ok", 1)
        if cache.get("health_check") == "ok":
            checks["cache"] = True
    except Exception:
        pass
    
    all_ready = all(checks.values())
    
    return JsonResponse(
        {
            "ready": all_ready,
            "checks": checks,
        },
        status=200 if all_ready else 503,
    )


# =============================================================================
# API URL PATTERNS
# =============================================================================

api_v1_patterns = [
    path("auth/", include("accounts.api.urls")),
    path("analysis/", include("detection.api.urls")),
    path("dashboard/", include("dashboard.api.urls")),
]

# =============================================================================
# MAIN URL PATTERNS
# =============================================================================

urlpatterns = [
    # Health check endpoints (no authentication required)
    path("health/", health_check, name="health-check"),
    path("health/ready/", ready_check, name="ready-check"),
    
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    
    # API v1
    path("api/v1/", include(api_v1_patterns)),
    
    # Web routes (detection app web views)
    path("", include("detection.web.urls", namespace="web")),
]

# =============================================================================
# CONDITIONAL URL PATTERNS
# =============================================================================

# Admin interface (always available, but secured)
urlpatterns.insert(0, path("admin/", admin.site.urls))

# Debug-specific URLs
if settings.DEBUG:
    # Django Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns.insert(0, path("__debug__/", include(debug_toolbar.urls)))
    except ImportError:
        pass

# Media files (development only - production uses nginx/CDN)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
