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
from django.shortcuts import redirect
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


def api_root(request) -> JsonResponse:
    """
    API root endpoint.
    
    Returns information about available API versions and documentation.
    """
    return JsonResponse({
        "message": "Aletheia API",
        "versions": {
            "v1": "/api/v1/",
        },
        "documentation": {
            "swagger": "/api/docs/",
            "redoc": "/api/redoc/",
            "schema": "/api/schema/",
        },
    })


def api_v1_root(request) -> JsonResponse:
    """
    API v1 root endpoint.
    
    Returns information about available v1 endpoints.
    """
    return JsonResponse({
        "version": "1.0",
        "endpoints": {
            "analysis": "/api/v1/analysis/",
            "auth": "/api/v1/auth/",
            "dashboard": "/api/v1/dashboard/",
        },
        "documentation": "/api/docs/",
    })


# =============================================================================
# API URL PATTERNS
# =============================================================================

api_v1_patterns = [
    path("", api_v1_root, name="api-v1-root"),
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
    
    # API Root (redirects to docs)
    path("api/", api_root, name="api-root"),
    
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
]

# =============================================================================
# CONDITIONAL URL PATTERNS
# =============================================================================

# Admin interface (always available, but secured)
urlpatterns.insert(0, path("admin/", admin.site.urls))

# Debug-specific URLs
if settings.DEBUG:
    from django.views.generic import TemplateView
    
    # Use development home page that doesn't require Vite
    urlpatterns.append(
        path("", TemplateView.as_view(template_name="dev_home.html"), name="home")
    )
    
    # Django Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns.insert(0, path("__debug__/", include(debug_toolbar.urls)))
    except ImportError:
        pass
else:
    # In production, serve React frontend
    urlpatterns.append(
        path("", include("detection.web.urls", namespace="web"))
    )

# Media files (development only - production uses nginx/CDN)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
