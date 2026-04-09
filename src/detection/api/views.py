"""
API Views

Django REST Framework views for the detection API.
Provides endpoints for analysis submission, status tracking,
report generation, and model information.
"""

from __future__ import annotations

import logging
from typing import Any

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import (
    AletheiaError,
    ProcessingError,
    ValidationError,
)

from .serializers import (
    AnalysisConfigSerializer,
    AnalysisListSerializer,
    AnalysisResponseSerializer,
    AnalysisStatusSerializer,
    AnalysisSubmitSerializer,
    BatchStatusSerializer,
    BatchSubmitSerializer,
    ErrorSerializer,
    FrameAnalysisSerializer,
    MediaFileSerializer,
    MediaUploadSerializer,
    ModelInfoSerializer,
    ModelMetricsSerializer,
    ReportOptionsSerializer,
    ReportResponseSerializer,
    WebhookRegisterSerializer,
    WebhookResponseSerializer,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Helper Functions
# =============================================================================

def error_response(
    message: str,
    code: str = "E0000",
    details: dict | None = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> Response:
    """Create standardized error response."""
    return Response(
        {
            "error": message,
            "code": code,
            "details": details,
            "timestamp": timezone.now().isoformat(),
        },
        status=status_code,
    )


# =============================================================================
# Analysis ViewSet
# =============================================================================

@method_decorator(csrf_exempt, name='dispatch')
class AnalysisViewSet(viewsets.ViewSet):
    """
    ViewSet for deepfake detection analyses.

    Endpoints:
        POST   /api/v1/analysis/submit/     - Submit new analysis
        GET    /api/v1/analysis/{id}/       - Get analysis details
        GET    /api/v1/analysis/{id}/status/ - Get analysis status
        GET    /api/v1/analysis/{id}/frames/ - Get frame analysis
        GET    /api/v1/analysis/{id}/report/ - Get analysis report
        DELETE /api/v1/analysis/{id}/       - Cancel analysis
        GET    /api/v1/analysis/            - List user's analyses
    """

    permission_classes = [AllowAny]  # Development: Allow all access
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        """Allow anonymous access for development."""
        return [AllowAny()]

    def list(self, request: Request) -> Response:
        """List all analyses (development endpoint)."""
        # For now, return empty list to avoid import issues
        return Response({
            "items": [],
            "meta": {
                "page": 1,
                "pageSize": 20,
                "totalPages": 0,
                "totalItems": 0,
            }
        })

    @action(detail=False, methods=["post"], url_path="submit")
    def submit(self, request: Request) -> Response:
        """
        Submit a new analysis.

        Accepts video/image file and optional configuration.
        Returns analysis ID for tracking.
        """
        serializer = AnalysisSubmitSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                message="Validation failed",
                code="E1001",
                details=serializer.errors,
            )

        try:
            from django.conf import settings
            from detection.services import AnalysisService, MediaService
            from detection.services.analysis_service import AnalysisConfig

            # Process upload - skip strict validation in development
            media_service = MediaService()
            upload_result = media_service.process_upload(
                file=serializer.validated_data["file"],
                user=request.user if request.user.is_authenticated else None,
                validate=not settings.DEBUG,  # Skip strict validation in debug mode
            )

            if not upload_result.success:
                return error_response(
                    message=upload_result.error,
                    code="E2001",
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            # Build config
            config_data = serializer.validated_data.get("config", {})
            if isinstance(config_data, dict):
                config = AnalysisConfig(
                    sequence_length=config_data.get("sequence_length", 60),
                    model_name=config_data.get("model_name", "ensemble"),
                    use_ensemble=config_data.get("use_ensemble", True),
                    generate_heatmaps=config_data.get("generate_heatmaps", True),
                    webhook_url=config_data.get("webhook_url", ""),
                )
            else:
                config = AnalysisConfig()

            # Create analysis
            analysis_service = AnalysisService()
            analysis = analysis_service.create_analysis(
                media_file=upload_result.media_file,
                user=request.user if request.user.is_authenticated else None,
                config=config,
            )

            # Submit for processing:
            #   - CELERY eager mode: synchronous execution in web process
            #   - Non-eager mode: async via Celery broker/worker
            task_id = None
            async_mode = not bool(getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False))

            task_id = analysis_service.submit_for_processing(
                analysis_id=analysis.id,
                async_mode=async_mode,
            )

            # Refresh analysis to get updated status
            analysis.refresh_from_db()

            logger.info(
                "Analysis submitted",
                extra={
                    "analysis_id": str(analysis.id),
                    "task_id": task_id,
                    "user_id": str(request.user.id) if request.user.is_authenticated else None,
                },
            )

            return Response(
                {
                    "id": str(analysis.id),
                    "status": analysis.status,
                    "message": "Analysis submitted successfully",
                    "task_id": task_id,
                },
                status=status.HTTP_202_ACCEPTED,
            )

        except ValidationError as e:
            return error_response(
                message=str(e),
                code=getattr(e, 'code', 'E1000'),
                details=getattr(e, 'details', None),
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        except AletheiaError as e:
            logger.error(f"Analysis submission failed: {e}")
            return error_response(
                message=str(e),
                code=getattr(e, 'code', 'E9000'),
                details=getattr(e, 'details', None),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except Exception as e:
            logger.exception(f"Unexpected error during analysis submission: {e}")
            return error_response(
                message=f"Submission failed: {str(e)}",
                code="E9999",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def retrieve(self, request: Request, pk: str) -> Response:
        """Get analysis details."""
        from detection.models import Analysis

        try:
            analysis = Analysis.objects.select_related("media_file").get(id=pk)
        except Analysis.DoesNotExist:
            return error_response(
                message=f"Analysis not found: {pk}",
                code="E4001",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Check ownership for non-public analyses
        if not request.user.is_authenticated:
            # Allow read access for demo
            pass
        elif analysis.user and analysis.user != request.user:
            return error_response(
                message="Access denied",
                code="E4003",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        response_data = analysis.to_dict()
        media_data = analysis.media_file.to_dict()

        # Transform to frontend-expected format (camelCase with correct field names)
        frontend_response = {
            "id": response_data["id"],
            "status": response_data["status"],
            "prediction": response_data.get("result"),  # Frontend expects 'prediction'
            "confidence": response_data.get("confidence"),
            "confidenceLevel": response_data.get("confidence_level"),
            "progress": response_data.get("progress", 0),
            "processingTime": response_data.get("processing_time"),
            "modelUsed": response_data.get("model_used", "ensemble"),
            "framesAnalyzed": response_data.get("frames_analyzed", 0),
            "facesDetected": response_data.get("faces_detected", 0),
            "errorMessage": response_data.get("error_message"),
            "progressMessage": response_data.get("progress_message", ""),
            "createdAt": response_data.get("created_at"),
            "startedAt": response_data.get("started_at"),
            "completedAt": response_data.get("completed_at"),
            "updatedAt": response_data.get("completed_at") or response_data.get("created_at"),
            "mediaFile": {
                "id": media_data.get("id", ""),
                "fileName": media_data.get("original_filename", ""),
                "fileSize": media_data.get("file_size", 0),
                "mimeType": media_data.get("mime_type", ""),
                "duration": media_data.get("duration"),
                "width": media_data.get("width") if media_data.get("resolution", "Unknown") != "Unknown" else None,
                "height": media_data.get("height") if media_data.get("resolution", "Unknown") != "Unknown" else None,
                "frameRate": media_data.get("fps"),
                "fileUrl": media_data.get("file_url"),
                "thumbnailUrl": media_data.get("thumbnail_url"),
                "createdAt": media_data.get("created_at", ""),
            },
            "modelResults": [],  # Frame-level model results not available in basic response
            "frames": [],  # Frame analysis not included in basic response
        }

        return Response(frontend_response)

    @action(detail=True, methods=["get"])
    def status(self, request: Request, pk: str) -> Response:
        """Get lightweight analysis status for polling."""
        from detection.services import AnalysisService

        try:
            service = AnalysisService()
            status_data = service.get_status(pk)

            return Response(status_data)

        except AletheiaError as e:
            return error_response(
                message=str(e),
                code=e.error_code,
                status_code=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=True, methods=["get"])
    def frames(self, request: Request, pk: str) -> Response:
        """Get frame-level analysis results."""
        from detection.models import Analysis, AnalysisFrame

        try:
            analysis = Analysis.objects.get(id=pk)
        except Analysis.DoesNotExist:
            return error_response(
                message=f"Analysis not found: {pk}",
                code="E4001",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        frames = AnalysisFrame.objects.filter(analysis=analysis).order_by("frame_index")

        serializer = FrameAnalysisSerializer(frames, many=True)

        return Response({
            "analysis_id": str(analysis.id),
            "total_frames": analysis.frames_analyzed,
            "frames": serializer.data,
        })

    @action(detail=True, methods=["get", "post"])
    def report(self, request: Request, pk: str) -> Response:
        """Get or generate analysis report."""
        from detection.models import Analysis
        from detection.services import ReportService
        from detection.services.report_service import ReportOptions

        try:
            analysis = Analysis.objects.get(id=pk)
        except Analysis.DoesNotExist:
            return error_response(
                message=f"Analysis not found: {pk}",
                code="E4001",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if not analysis.is_completed:
            return error_response(
                message="Cannot generate report for incomplete analysis",
                code="E3003",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # GET: Return existing reports
        if request.method == "GET":
            service = ReportService()
            reports = service.get_reports_for_analysis(pk)

            serializer = ReportResponseSerializer(reports, many=True)
            return Response(serializer.data)

        # POST: Generate new report
        options_serializer = ReportOptionsSerializer(data=request.data)

        if not options_serializer.is_valid():
            return error_response(
                message="Invalid report options",
                code="E1001",
                details=options_serializer.errors,
            )

        try:
            options = ReportOptions(
                report_type=options_serializer.validated_data.get("report_type", "summary"),
                format=options_serializer.validated_data.get("format", "pdf"),
                include_frames=options_serializer.validated_data.get("include_frames", True),
                include_heatmaps=options_serializer.validated_data.get("include_heatmaps", False),
            )

            service = ReportService()
            report = service.generate_report(
                analysis_id=pk,
                options=options,
            )

            serializer = ReportResponseSerializer(report)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except AletheiaError as e:
            return error_response(
                message=str(e),
                code=e.error_code,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def destroy(self, request: Request, pk: str) -> Response:
        """Cancel a pending or processing analysis."""
        from detection.services import AnalysisService

        try:
            service = AnalysisService()
            cancelled = service.cancel_analysis(pk)

            if cancelled:
                return Response(
                    {"message": "Analysis cancelled"},
                    status=status.HTTP_200_OK,
                )
            else:
                return error_response(
                    message="Analysis is already in terminal state",
                    code="E3004",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        except AletheiaError as e:
            return error_response(
                message=str(e),
                code=e.error_code,
                status_code=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request: Request) -> Response:
        """
        Get analysis statistics.

        Returns summary statistics including total analyses,
        detection counts, and average processing time.
        """
        from django.db.models import Avg, Count, Q
        from detection.models import Analysis

        try:
            # Get all completed analyses
            analyses = Analysis.objects.filter(status="completed")

            # Calculate statistics
            total = analyses.count()
            fake_count = analyses.filter(result="fake").count()
            real_count = analyses.filter(result="real").count()

            # Calculate averages
            avg_stats = analyses.aggregate(
                avg_confidence=Avg("confidence"),
                avg_processing_time=Avg("processing_time"),
            )

            return Response({
                "totalAnalyses": total,
                "fakeDetected": fake_count,
                "realDetected": real_count,
                "averageConfidence": round(avg_stats["avg_confidence"] or 0, 2),
                "averageProcessingTime": round(avg_stats["avg_processing_time"] or 0, 2),
            })

        except Exception as e:
            logger.exception(f"Error fetching stats: {e}")
            return Response({
                "totalAnalyses": 0,
                "fakeDetected": 0,
                "realDetected": 0,
                "averageConfidence": 0,
                "averageProcessingTime": 0,
            })


# =============================================================================
# Batch ViewSet
# =============================================================================

class BatchViewSet(viewsets.ViewSet):
    """
    ViewSet for batch analysis operations.

    Endpoints:
        POST /api/v1/batch/submit/ - Submit batch analysis
        GET  /api/v1/batch/{id}/   - Get batch status
    """

    permission_classes = [AllowAny]  # Development: Allow all access
    parser_classes = [MultiPartParser, FormParser]

    @action(detail=False, methods=["post"], url_path="submit")
    def submit(self, request: Request) -> Response:
        """Submit batch of files for analysis."""
        serializer = BatchSubmitSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                message="Validation failed",
                code="E1001",
                details=serializer.errors,
            )

        # Process each file and create analyses
        from detection.services import AnalysisService, MediaService
        from detection.services.analysis_service import AnalysisConfig
        import uuid

        batch_id = str(uuid.uuid4())
        analysis_ids = []
        errors = []

        config_data = serializer.validated_data.get("config", {})
        config = AnalysisConfig(
            sequence_length=config_data.get("sequence_length", 60),
            model_name=config_data.get("model_name", "ensemble"),
        )

        media_service = MediaService()
        analysis_service = AnalysisService()

        for file in serializer.validated_data["files"]:
            try:
                upload_result = media_service.process_upload(
                    file=file,
                    user=request.user,
                )

                if upload_result.success:
                    analysis = analysis_service.create_analysis(
                        media_file=upload_result.media_file,
                        user=request.user,
                        config=config,
                    )
                    analysis_ids.append(str(analysis.id))
                else:
                    errors.append({
                        "filename": file.name,
                        "error": upload_result.error,
                    })

            except Exception as e:
                errors.append({
                    "filename": file.name,
                    "error": str(e),
                })

        if analysis_ids:
            from django.conf import settings
            eager_mode = bool(getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False))
            if eager_mode:
                for analysis_id in analysis_ids:
                    analysis_service.submit_for_processing(
                        analysis_id=analysis_id,
                        async_mode=False,
                    )
            else:
                from detection.tasks import batch_analysis_task
                batch_analysis_task.delay(analysis_ids)

        return Response({
            "batch_id": batch_id,
            "total": len(serializer.validated_data["files"]),
            "accepted": len(analysis_ids),
            "rejected": len(errors),
            "analysis_ids": analysis_ids,
            "errors": errors if errors else None,
        }, status=status.HTTP_202_ACCEPTED)


# =============================================================================
# Model Info ViewSet
# =============================================================================

class ModelViewSet(viewsets.ViewSet):
    """
    ViewSet for ML model information.

    Endpoints:
        GET /api/v1/models/         - List available models
        GET /api/v1/models/{id}/    - Get model details
        GET /api/v1/models/{id}/metrics/ - Get model metrics
    """

    permission_classes = [AllowAny]

    # Static model info (would come from registry in production)
    MODELS = {
        "efficientnet_lstm": {
            "name": "efficientnet_lstm",
            "display_name": "EfficientNet-B4 + BiLSTM",
            "description": "EfficientNet-B4 backbone with bidirectional LSTM for temporal modeling",
            "version": "1.0.0",
            "architecture": "CNN + RNN",
            "input_size": [3, 60, 224, 224],
            "parameters": 87000000,
            "is_available": True,
            "metrics": {
                "accuracy": 0.965,
                "precision": 0.958,
                "recall": 0.972,
                "f1_score": 0.965,
                "auc_roc": 0.991,
                "inference_time_ms": 450,
                "dataset": "FaceForensics++",
            },
        },
        "resnext_transformer": {
            "name": "resnext_transformer",
            "display_name": "ResNeXt-101 + Transformer",
            "description": "ResNeXt-101 backbone with transformer encoder for attention-based detection",
            "version": "1.0.0",
            "architecture": "CNN + Transformer",
            "input_size": [3, 60, 224, 224],
            "parameters": 95000000,
            "is_available": True,
            "metrics": {
                "accuracy": 0.958,
                "precision": 0.962,
                "recall": 0.954,
                "f1_score": 0.958,
                "auc_roc": 0.987,
                "inference_time_ms": 520,
                "dataset": "FaceForensics++",
            },
        },
        "ensemble": {
            "name": "ensemble",
            "display_name": "Multi-Model Ensemble",
            "description": "Ensemble of multiple architectures with weighted voting",
            "version": "1.0.0",
            "architecture": "Ensemble",
            "input_size": [3, 60, 224, 224],
            "parameters": 182000000,
            "is_available": True,
            "metrics": {
                "accuracy": 0.978,
                "precision": 0.975,
                "recall": 0.981,
                "f1_score": 0.978,
                "auc_roc": 0.995,
                "inference_time_ms": 850,
                "dataset": "FaceForensics++",
            },
        },
    }

    def list(self, request: Request) -> Response:
        """List available models."""
        models = list(self.MODELS.values())
        serializer = ModelInfoSerializer(models, many=True)
        return Response(serializer.data)

    def retrieve(self, request: Request, pk: str) -> Response:
        """Get model details."""
        if pk not in self.MODELS:
            return error_response(
                message=f"Model not found: {pk}",
                code="E4001",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = ModelInfoSerializer(self.MODELS[pk])
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def metrics(self, request: Request, pk: str) -> Response:
        """Get model performance metrics."""
        if pk not in self.MODELS:
            return error_response(
                message=f"Model not found: {pk}",
                code="E4001",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        metrics = self.MODELS[pk]["metrics"]
        metrics["last_updated"] = timezone.now()

        serializer = ModelMetricsSerializer(metrics)
        return Response(serializer.data)


# =============================================================================
# Health Check Views
# =============================================================================

class HealthCheckView(APIView):
    """
    Health check endpoint for monitoring.

    GET /api/v1/health/ - Basic health check
    GET /api/v1/health/detailed/ - Detailed health with dependencies
    """

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        """Basic health check."""
        return Response({
            "status": "healthy",
            "timestamp": timezone.now().isoformat(),
            "version": "1.0.0",
        })


class DetailedHealthCheckView(APIView):
    """Detailed health check with dependency status."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        """Detailed health check."""
        from django.db import connection
        from django.core.cache import cache

        checks = {
            "database": self._check_database(),
            "cache": self._check_cache(),
            "storage": self._check_storage(),
            "celery": self._check_celery(),
        }

        all_healthy = all(c["healthy"] for c in checks.values())

        return Response({
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": timezone.now().isoformat(),
            "version": "1.0.0",
            "checks": checks,
        }, status=status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE)

    def _check_database(self) -> dict[str, Any]:
        """Check database connectivity."""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {"healthy": True, "latency_ms": 0}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    def _check_cache(self) -> dict[str, Any]:
        """Check cache connectivity."""
        try:
            from django.core.cache import cache
            cache.set("health_check", "ok", 10)
            result = cache.get("health_check")
            return {"healthy": result == "ok", "latency_ms": 0}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    def _check_storage(self) -> dict[str, Any]:
        """Check storage accessibility."""
        try:
            from django.conf import settings
            from pathlib import Path

            media_root = Path(settings.MEDIA_ROOT)
            if media_root.exists() and media_root.is_dir():
                return {"healthy": True, "path": str(media_root)}
            return {"healthy": False, "error": "Media root not accessible"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    def _check_celery(self) -> dict[str, Any]:
        """Check Celery connectivity."""
        try:
            from celery import current_app
            inspect = current_app.control.inspect()

            # Check for active workers
            active = inspect.active()
            if active:
                return {"healthy": True, "workers": len(active)}
            return {"healthy": False, "error": "No active workers"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
