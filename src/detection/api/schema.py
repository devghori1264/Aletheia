"""
OpenAPI schema generation for Aletheia API.

This module provides utilities for generating and customizing
the OpenAPI schema for the Aletheia REST API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.conf import settings
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

if TYPE_CHECKING:
    from rest_framework.request import Request


# =============================================================================
# SCHEMA CONFIGURATION
# =============================================================================


SPECTACULAR_SETTINGS: dict[str, Any] = {
    "TITLE": "Aletheia API",
    "DESCRIPTION": """
# Aletheia - Enterprise-Grade Deepfake Detection API

Aletheia provides state-of-the-art deepfake detection using advanced machine learning models.

## Features

- **Multi-model Ensemble**: Combines multiple detection models for higher accuracy
- **Real-time Analysis**: Fast inference with GPU acceleration
- **Explainable AI**: GradCAM++ heatmaps for visual explanations
- **Batch Processing**: Analyze multiple files simultaneously
- **Webhook Support**: Get notified when analysis completes

## Authentication

All endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_access_token>
```

## Rate Limiting

- Free tier: 10 requests/minute, 100 requests/day
- Pro tier: 60 requests/minute, 5,000 requests/day
- Enterprise: Custom limits

## Error Handling

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {...}
  }
}
```
    """,
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "CONTACT": {
        "name": "Aletheia Support",
        "email": "support@aletheia.io",
        "url": "https://aletheia.io/support",
    },
    "LICENSE": {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    "EXTERNAL_DOCS": {
        "description": "Full documentation",
        "url": "https://docs.aletheia.io",
    },
    "TAGS": [
        {
            "name": "Authentication",
            "description": "User authentication and token management",
        },
        {
            "name": "Analysis",
            "description": "Submit and retrieve deepfake analysis",
        },
        {
            "name": "Batch",
            "description": "Batch processing operations",
        },
        {
            "name": "Models",
            "description": "ML model information and metrics",
        },
        {
            "name": "Health",
            "description": "Health check endpoints",
        },
    ],
    "COMPONENT_SPLIT_REQUEST": True,
    "COMPONENT_NO_READ_ONLY_REQUIRED": True,
    "ENUM_NAME_OVERRIDES": {
        "AnalysisStatusEnum": "detection.models.analysis.AnalysisStatus",
        "PredictionEnum": "detection.models.analysis.Prediction",
    },
    "PREPROCESSING_HOOKS": [
        "detection.api.schema.preprocessing_filter_spec",
    ],
    "POSTPROCESSING_HOOKS": [
        "detection.api.schema.postprocessing_add_security",
    ],
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]+",
    "SERVERS": [
        {
            "url": "https://api.aletheia.io/v1",
            "description": "Production server",
        },
        {
            "url": "https://staging-api.aletheia.io/v1",
            "description": "Staging server",
        },
        {
            "url": "http://localhost:8000/api/v1",
            "description": "Local development",
        },
    ],
    "SECURITY": [{"Bearer": []}],
}


# =============================================================================
# CUSTOM SCHEMA EXTENSIONS
# =============================================================================


class JWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """Custom authentication scheme for JWT."""

    target_class = "rest_framework_simplejwt.authentication.JWTAuthentication"
    name = "Bearer"

    def get_security_definition(
        self,
        auto_schema: AutoSchema,
    ) -> dict[str, Any]:
        """Return JWT security definition."""
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT access token",
        }


# =============================================================================
# SCHEMA HOOKS
# =============================================================================


def preprocessing_filter_spec(
    endpoints: list[tuple[str, str, str, Any]],
) -> list[tuple[str, str, str, Any]]:
    """
    Filter and preprocess endpoints before schema generation.

    Args:
        endpoints: List of (path, method, view_cls, view) tuples.

    Returns:
        Filtered list of endpoints.
    """
    # Filter out internal endpoints
    filtered = []
    for path, method, view_cls, view in endpoints:
        # Skip admin and debug endpoints
        if path.startswith("/admin/") or path.startswith("/__debug__/"):
            continue
        filtered.append((path, method, view_cls, view))

    return filtered


def postprocessing_add_security(
    result: dict[str, Any],
    generator: SchemaGenerator,
    request: Request | None,
    public: bool,
) -> dict[str, Any]:
    """
    Post-process the schema to add security requirements.

    Args:
        result: Generated schema dictionary.
        generator: Schema generator instance.
        request: Optional request object.
        public: Whether the schema is public.

    Returns:
        Modified schema dictionary.
    """
    # Add security schemes
    result["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT access token obtained from /auth/token/",
        },
        "ApiKey": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for programmatic access",
        },
    }

    # Add global security requirement
    result["security"] = [{"Bearer": []}, {"ApiKey": []}]

    return result


# =============================================================================
# REUSABLE SCHEMA COMPONENTS
# =============================================================================


# Common parameters
ANALYSIS_ID_PARAM = OpenApiParameter(
    name="id",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.PATH,
    description="Unique analysis identifier (UUID)",
    required=True,
)

BATCH_ID_PARAM = OpenApiParameter(
    name="batch_id",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.PATH,
    description="Unique batch identifier",
    required=True,
)

PAGE_PARAM = OpenApiParameter(
    name="page",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    description="Page number for pagination",
    default=1,
)

PAGE_SIZE_PARAM = OpenApiParameter(
    name="page_size",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    description="Number of items per page (max 100)",
    default=20,
)


# Common responses
ERROR_400_RESPONSE = OpenApiResponse(
    description="Bad Request - Invalid input",
    response={"type": "object"},
    examples=[
        OpenApiExample(
            name="Validation Error",
            value={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "File size exceeds maximum allowed",
                    "details": {
                        "field": "file",
                        "max_size": 524288000,
                    },
                },
            },
        ),
    ],
)

ERROR_401_RESPONSE = OpenApiResponse(
    description="Unauthorized - Authentication required",
    response={"type": "object"},
    examples=[
        OpenApiExample(
            name="Missing Token",
            value={
                "error": {
                    "code": "AUTHENTICATION_ERROR",
                    "message": "Authentication credentials were not provided",
                },
            },
        ),
    ],
)

ERROR_404_RESPONSE = OpenApiResponse(
    description="Not Found - Resource does not exist",
    response={"type": "object"},
    examples=[
        OpenApiExample(
            name="Not Found",
            value={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Analysis not found",
                },
            },
        ),
    ],
)

ERROR_429_RESPONSE = OpenApiResponse(
    description="Too Many Requests - Rate limit exceeded",
    response={"type": "object"},
    examples=[
        OpenApiExample(
            name="Rate Limited",
            value={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Rate limit exceeded. Retry after 60 seconds",
                    "details": {
                        "retry_after": 60,
                    },
                },
            },
        ),
    ],
)

ERROR_500_RESPONSE = OpenApiResponse(
    description="Internal Server Error",
    response={"type": "object"},
    examples=[
        OpenApiExample(
            name="Server Error",
            value={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                },
            },
        ),
    ],
)


# =============================================================================
# SCHEMA DECORATORS FOR VIEWS
# =============================================================================

# Analysis endpoints
analysis_list_schema = extend_schema(
    summary="List analyses",
    description="Retrieve paginated list of all analyses for the authenticated user.",
    parameters=[PAGE_PARAM, PAGE_SIZE_PARAM],
    responses={
        200: OpenApiResponse(description="List of analyses"),
        401: ERROR_401_RESPONSE,
    },
    tags=["Analysis"],
)

analysis_create_schema = extend_schema(
    summary="Submit analysis",
    description="""
Submit a video or image file for deepfake analysis.

**Supported formats:**
- Video: MP4, AVI, MOV, MKV, WebM
- Image: JPG, JPEG, PNG, WebP

**Size limits:**
- Maximum file size: 500MB
- Maximum video duration: 5 minutes

The analysis runs asynchronously. Poll the returned ID or configure a webhook
to be notified when complete.
    """,
    request={
        "multipart/form-data": {
            "type": "object",
            "properties": {
                "file": {
                    "type": "string",
                    "format": "binary",
                    "description": "Video or image file to analyze",
                },
                "options": {
                    "type": "object",
                    "description": "Analysis options",
                    "properties": {
                        "use_ensemble": {"type": "boolean", "default": True},
                        "generate_heatmaps": {"type": "boolean", "default": True},
                        "webhook_url": {"type": "string", "format": "uri"},
                    },
                },
            },
            "required": ["file"],
        },
    },
    responses={
        202: OpenApiResponse(description="Analysis submitted successfully"),
        400: ERROR_400_RESPONSE,
        401: ERROR_401_RESPONSE,
        429: ERROR_429_RESPONSE,
    },
    tags=["Analysis"],
    examples=[
        OpenApiExample(
            name="Accepted Response",
            response_only=True,
            value={
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "pending",
                "progress": 0,
                "created_at": "2024-01-15T10:30:00Z",
            },
        ),
    ],
)

analysis_retrieve_schema = extend_schema(
    summary="Get analysis details",
    description="Retrieve detailed results for a specific analysis.",
    parameters=[ANALYSIS_ID_PARAM],
    responses={
        200: OpenApiResponse(description="Analysis details"),
        401: ERROR_401_RESPONSE,
        404: ERROR_404_RESPONSE,
    },
    tags=["Analysis"],
)

analysis_cancel_schema = extend_schema(
    summary="Cancel analysis",
    description="Cancel a pending or in-progress analysis.",
    parameters=[ANALYSIS_ID_PARAM],
    responses={
        200: OpenApiResponse(description="Analysis cancelled"),
        400: ERROR_400_RESPONSE,
        401: ERROR_401_RESPONSE,
        404: ERROR_404_RESPONSE,
    },
    tags=["Analysis"],
)


# Health endpoints
health_check_schema = extend_schema(
    summary="Health check",
    description="Check the health status of the API and its dependencies.",
    responses={
        200: OpenApiResponse(
            description="API is healthy",
            examples=[
                OpenApiExample(
                    name="Healthy",
                    value={
                        "status": "healthy",
                        "version": "1.0.0",
                        "services": {
                            "database": "up",
                            "redis": "up",
                            "ml_models": "loaded",
                        },
                    },
                ),
            ],
        ),
        503: OpenApiResponse(
            description="API is unhealthy",
            examples=[
                OpenApiExample(
                    name="Unhealthy",
                    value={
                        "status": "unhealthy",
                        "version": "1.0.0",
                        "services": {
                            "database": "up",
                            "redis": "down",
                            "ml_models": "loaded",
                        },
                    },
                ),
            ],
        ),
    },
    tags=["Health"],
    auth=[],
)


# =============================================================================
# SCHEMA GENERATION UTILITIES
# =============================================================================


def generate_schema_json() -> str:
    """
    Generate OpenAPI schema as JSON string.

    Returns:
        JSON string of the OpenAPI schema.
    """
    import json

    from drf_spectacular.generators import SchemaGenerator

    generator = SchemaGenerator(patterns=None, urlconf=None)
    schema = generator.get_schema(request=None, public=True)

    return json.dumps(schema, indent=2)


def generate_schema_yaml() -> str:
    """
    Generate OpenAPI schema as YAML string.

    Returns:
        YAML string of the OpenAPI schema.
    """
    import yaml

    from drf_spectacular.generators import SchemaGenerator

    generator = SchemaGenerator(patterns=None, urlconf=None)
    schema = generator.get_schema(request=None, public=True)

    return yaml.dump(schema, default_flow_style=False)


__all__ = [
    "SPECTACULAR_SETTINGS",
    "JWTAuthenticationScheme",
    "preprocessing_filter_spec",
    "postprocessing_add_security",
    "ANALYSIS_ID_PARAM",
    "BATCH_ID_PARAM",
    "PAGE_PARAM",
    "PAGE_SIZE_PARAM",
    "ERROR_400_RESPONSE",
    "ERROR_401_RESPONSE",
    "ERROR_404_RESPONSE",
    "ERROR_429_RESPONSE",
    "ERROR_500_RESPONSE",
    "analysis_list_schema",
    "analysis_create_schema",
    "analysis_retrieve_schema",
    "analysis_cancel_schema",
    "health_check_schema",
    "generate_schema_json",
    "generate_schema_yaml",
]
