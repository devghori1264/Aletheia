"""
Report Service

Generates comprehensive analysis reports in multiple formats.
Supports PDF, JSON, CSV, and HTML output with customizable templates.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Final, TYPE_CHECKING
from uuid import UUID

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from core.exceptions import (
    ProcessingError,
    ValidationError,
)

if TYPE_CHECKING:
    from detection.models import Analysis, Report

logger = logging.getLogger(__name__)


# =============================================================================
# Type Definitions
# =============================================================================

@dataclass(frozen=True, slots=True)
class ReportOptions:
    """
    Options for report generation.
    
    Attributes:
        report_type: Type of report (summary/detailed/technical/executive)
        format: Output format (pdf/json/csv/html)
        include_frames: Include frame-level details
        include_heatmaps: Include attention heatmaps
        include_graphs: Include visualization graphs
        language: Report language
    """
    
    report_type: str = "summary"
    format: str = "pdf"
    include_frames: bool = True
    include_heatmaps: bool = False
    include_graphs: bool = True
    language: str = "en"
    expiry_hours: int = 24
    
    def __post_init__(self):
        """Validate options."""
        valid_types = {"summary", "detailed", "technical", "executive"}
        valid_formats = {"pdf", "json", "csv", "html"}
        
        if self.report_type not in valid_types:
            raise ValueError(f"Invalid report type: {self.report_type}")
        if self.format not in valid_formats:
            raise ValueError(f"Invalid format: {self.format}")


@dataclass
class ReportData:
    """
    Compiled data for report generation.
    
    Contains all information needed to render a report.
    """
    
    analysis_id: str
    media_filename: str
    result: str
    confidence: float
    confidence_level: str
    frames_analyzed: int
    faces_detected: int
    processing_time: float
    model_used: str
    created_at: datetime
    completed_at: datetime | None
    frame_predictions: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_analysis(cls, analysis: "Analysis") -> "ReportData":
        """Create ReportData from Analysis model."""
        return cls(
            analysis_id=str(analysis.id),
            media_filename=analysis.media_file.original_filename,
            result=analysis.result or "pending",
            confidence=analysis.confidence or 0.0,
            confidence_level=analysis.confidence_level or "unknown",
            frames_analyzed=analysis.frames_analyzed,
            faces_detected=analysis.faces_detected,
            processing_time=analysis.processing_time or 0.0,
            model_used=analysis.model_used,
            created_at=analysis.created_at,
            completed_at=analysis.completed_at,
            frame_predictions=analysis.metadata.get("frame_predictions", []),
            metadata=analysis.metadata,
        )


# =============================================================================
# Report Service
# =============================================================================

class ReportService:
    """
    Service for generating analysis reports.
    
    Provides operations for:
        - Generating reports in multiple formats
        - Customizing report content
        - Managing report access
        - Tracking downloads
    
    Example:
        >>> service = ReportService()
        >>> report = service.generate_report(
        ...     analysis_id=analysis.id,
        ...     options=ReportOptions(
        ...         report_type="detailed",
        ...         format="pdf",
        ...     ),
        ... )
    """
    
    # Report type configurations
    REPORT_CONFIGS: Final[dict[str, dict[str, Any]]] = {
        "summary": {
            "template": "reports/summary.html",
            "title": "Deepfake Detection Summary",
            "sections": ["overview", "result", "recommendations"],
        },
        "detailed": {
            "template": "reports/detailed.html",
            "title": "Detailed Analysis Report",
            "sections": ["overview", "result", "frames", "methodology", "recommendations"],
        },
        "technical": {
            "template": "reports/technical.html",
            "title": "Technical Analysis Report",
            "sections": ["overview", "result", "frames", "model", "metrics", "raw_data"],
        },
        "executive": {
            "template": "reports/executive.html",
            "title": "Executive Summary",
            "sections": ["overview", "result", "key_findings"],
        },
    }
    
    def __init__(
        self,
        output_dir: Path | None = None,
    ):
        """
        Initialize the report service.
        
        Args:
            output_dir: Custom output directory for reports
        """
        self._output_dir = output_dir or Path(settings.MEDIA_ROOT) / "reports"
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Ensure output directory exists
        self._output_dir.mkdir(parents=True, exist_ok=True)
    
    # =========================================================================
    # Report Generation
    # =========================================================================
    
    def generate_report(
        self,
        analysis_id: UUID | str,
        options: ReportOptions | None = None,
    ) -> "Report":
        """
        Generate a report for an analysis.
        
        Args:
            analysis_id: Analysis to generate report for
            options: Report generation options
        
        Returns:
            Generated Report instance
        
        Raises:
            ProcessingError: If generation fails
        """
        from detection.models import Analysis, Report
        import time
        
        options = options or ReportOptions()
        start_time = time.time()
        
        # Get analysis
        try:
            analysis = Analysis.objects.select_related("media_file").get(id=analysis_id)
        except Analysis.DoesNotExist:
            raise ProcessingError(
                f"Analysis not found: {analysis_id}",
                details={"analysis_id": str(analysis_id)},
            )
        
        # Check if analysis is complete
        if not analysis.is_completed:
            raise ProcessingError(
                f"Cannot generate report for incomplete analysis",
                details={
                    "analysis_id": str(analysis_id),
                    "status": analysis.status,
                },
            )
        
        # Compile report data
        data = ReportData.from_analysis(analysis)
        
        # Generate content based on format
        if options.format == "json":
            content, file_content = self._generate_json_report(data, options)
        elif options.format == "csv":
            content, file_content = self._generate_csv_report(data, options)
        elif options.format == "html":
            content, file_content = self._generate_html_report(data, options)
        elif options.format == "pdf":
            content, file_content = self._generate_pdf_report(data, options)
        else:
            raise ValueError(f"Unsupported format: {options.format}")
        
        # Create report record
        report = Report.objects.create(
            analysis=analysis,
            report_type=options.report_type,
            format=options.format,
            content=content if options.format == "json" else {},
            generated_by="system",
            generation_time=time.time() - start_time,
            options={
                "include_frames": options.include_frames,
                "include_heatmaps": options.include_heatmaps,
                "include_graphs": options.include_graphs,
            },
        )
        
        # Save file if generated
        if file_content:
            filename = report.filename
            report.file.save(filename, file_content, save=True)
            report.file_size = report.file.size
            report.save(update_fields=["file_size"])
        
        # Set expiration
        if options.expiry_hours > 0:
            report.set_expiration(hours=options.expiry_hours)
        
        self._logger.info(
            "Report generated",
            extra={
                "report_id": str(report.id),
                "analysis_id": str(analysis_id),
                "format": options.format,
                "type": options.report_type,
                "generation_time": report.generation_time,
            },
        )
        
        return report
    
    # =========================================================================
    # Format-Specific Generators
    # =========================================================================
    
    def _generate_json_report(
        self,
        data: ReportData,
        options: ReportOptions,
    ) -> tuple[dict[str, Any], BytesIO | None]:
        """Generate JSON format report."""
        content = {
            "report_type": options.report_type,
            "generated_at": timezone.now().isoformat(),
            "analysis": {
                "id": data.analysis_id,
                "media_filename": data.media_filename,
                "result": data.result,
                "confidence": data.confidence,
                "confidence_level": data.confidence_level,
                "frames_analyzed": data.frames_analyzed,
                "faces_detected": data.faces_detected,
                "processing_time_seconds": data.processing_time,
                "model_used": data.model_used,
                "created_at": data.created_at.isoformat(),
                "completed_at": data.completed_at.isoformat() if data.completed_at else None,
            },
            "summary": self._generate_summary_text(data),
            "recommendations": self._generate_recommendations(data),
        }
        
        # Include frame-level data if requested
        if options.include_frames and data.frame_predictions:
            content["frames"] = data.frame_predictions
        
        # Include metadata if technical report
        if options.report_type == "technical":
            content["metadata"] = data.metadata
        
        # Generate file content
        json_bytes = json.dumps(content, indent=2, ensure_ascii=False).encode("utf-8")
        file_content = BytesIO(json_bytes)
        
        return content, file_content
    
    def _generate_csv_report(
        self,
        data: ReportData,
        options: ReportOptions,
    ) -> tuple[dict[str, Any], BytesIO | None]:
        """Generate CSV format report."""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Analysis ID", "Media File", "Result", "Confidence (%)",
            "Confidence Level", "Frames Analyzed", "Faces Detected",
            "Processing Time (s)", "Model Used", "Created At", "Completed At"
        ])
        
        # Main row
        writer.writerow([
            data.analysis_id,
            data.media_filename,
            data.result,
            f"{data.confidence:.2f}",
            data.confidence_level,
            data.frames_analyzed,
            data.faces_detected,
            f"{data.processing_time:.2f}",
            data.model_used,
            data.created_at.isoformat(),
            data.completed_at.isoformat() if data.completed_at else "",
        ])
        
        # Frame-level data if requested
        if options.include_frames and data.frame_predictions:
            writer.writerow([])
            writer.writerow(["Frame Analysis"])
            writer.writerow(["Frame Index", "Prediction", "Confidence"])
            
            for frame in data.frame_predictions:
                writer.writerow([
                    frame.get("frame_index", ""),
                    frame.get("prediction", ""),
                    f"{frame.get('confidence', 0):.4f}",
                ])
        
        # Convert to bytes
        csv_content = output.getvalue()
        file_content = BytesIO(csv_content.encode("utf-8"))
        
        return {}, file_content
    
    def _generate_html_report(
        self,
        data: ReportData,
        options: ReportOptions,
    ) -> tuple[dict[str, Any], BytesIO | None]:
        """Generate HTML format report."""
        config = self.REPORT_CONFIGS[options.report_type]
        
        context = {
            "report_title": config["title"],
            "report_type": options.report_type,
            "sections": config["sections"],
            "data": data,
            "summary": self._generate_summary_text(data),
            "recommendations": self._generate_recommendations(data),
            "generated_at": timezone.now(),
            "options": options,
        }
        
        # Try to render from template
        try:
            html_content = render_to_string(config["template"], context)
        except Exception:
            # Fallback to inline template
            html_content = self._generate_inline_html(context)
        
        file_content = BytesIO(html_content.encode("utf-8"))
        
        return {}, file_content
    
    def _generate_inline_html(self, context: dict[str, Any]) -> str:
        """Generate HTML using inline template."""
        data = context["data"]
        
        result_color = {
            "fake": "#dc3545",
            "real": "#28a745",
            "uncertain": "#ffc107",
        }.get(data.result, "#6c757d")
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{context['report_title']} - Aletheia</title>
    <style>
        :root {{
            --primary-color: #6366f1;
            --success-color: #28a745;
            --danger-color: #dc3545;
            --warning-color: #ffc107;
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-color: #e2e8f0;
            --text-muted: #94a3b8;
            --border-color: #334155;
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            padding: 2rem;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #6366f1, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}
        
        .header .subtitle {{
            color: var(--text-muted);
            font-size: 1.1rem;
        }}
        
        .card {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid var(--border-color);
        }}
        
        .card h2 {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--primary-color);
        }}
        
        .result-badge {{
            display: inline-block;
            padding: 0.75rem 2rem;
            border-radius: 9999px;
            font-size: 1.5rem;
            font-weight: 700;
            text-transform: uppercase;
            color: white;
            background: {result_color};
            margin: 1rem 0;
        }}
        
        .confidence-bar {{
            height: 12px;
            background: var(--border-color);
            border-radius: 6px;
            overflow: hidden;
            margin: 1rem 0;
        }}
        
        .confidence-fill {{
            height: 100%;
            background: linear-gradient(90deg, #6366f1, #a855f7);
            width: {data.confidence}%;
            transition: width 0.5s ease;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1.5rem 0;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 1rem;
            background: rgba(99, 102, 241, 0.1);
            border-radius: 8px;
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary-color);
        }}
        
        .stat-label {{
            font-size: 0.875rem;
            color: var(--text-muted);
            margin-top: 0.25rem;
        }}
        
        .info-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .info-table tr {{
            border-bottom: 1px solid var(--border-color);
        }}
        
        .info-table tr:last-child {{
            border-bottom: none;
        }}
        
        .info-table th {{
            text-align: left;
            padding: 0.75rem 0;
            color: var(--text-muted);
            font-weight: 500;
            width: 40%;
        }}
        
        .info-table td {{
            padding: 0.75rem 0;
        }}
        
        .recommendations {{
            margin-top: 1rem;
        }}
        
        .recommendation-item {{
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
            padding: 0.75rem 0;
        }}
        
        .recommendation-item::before {{
            content: "→";
            color: var(--primary-color);
            font-weight: bold;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid var(--border-color);
            color: var(--text-muted);
            font-size: 0.875rem;
        }}
        
        .logo {{
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--primary-color);
        }}
        
        @media print {{
            body {{
                background: white;
                color: #1a1a1a;
                padding: 1rem;
            }}
            
            .card {{
                background: #f8f9fa;
                border: 1px solid #dee2e6;
            }}
            
            .header h1 {{
                background: none;
                -webkit-text-fill-color: #6366f1;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="logo">⬡ ALETHEIA</div>
            <h1>{context['report_title']}</h1>
            <p class="subtitle">Analysis ID: {data.analysis_id[:8]}...</p>
        </header>
        
        <div class="card">
            <h2>Detection Result</h2>
            <div style="text-align: center;">
                <span class="result-badge">{data.result.upper()}</span>
                <div class="confidence-bar">
                    <div class="confidence-fill"></div>
                </div>
                <p style="color: var(--text-muted);">
                    Confidence: <strong>{data.confidence:.1f}%</strong> ({data.confidence_level})
                </p>
            </div>
        </div>
        
        <div class="card">
            <h2>Analysis Statistics</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">{data.frames_analyzed}</div>
                    <div class="stat-label">Frames Analyzed</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{data.faces_detected}</div>
                    <div class="stat-label">Faces Detected</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{data.processing_time:.1f}s</div>
                    <div class="stat-label">Processing Time</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>File Information</h2>
            <table class="info-table">
                <tr>
                    <th>Media File</th>
                    <td>{data.media_filename}</td>
                </tr>
                <tr>
                    <th>Model Used</th>
                    <td>{data.model_used}</td>
                </tr>
                <tr>
                    <th>Submitted At</th>
                    <td>{data.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
                </tr>
                <tr>
                    <th>Completed At</th>
                    <td>{data.completed_at.strftime('%Y-%m-%d %H:%M:%S UTC') if data.completed_at else 'N/A'}</td>
                </tr>
            </table>
        </div>
        
        <div class="card">
            <h2>Summary</h2>
            <p>{context['summary']}</p>
        </div>
        
        <div class="card">
            <h2>Recommendations</h2>
            <div class="recommendations">
                {"".join(f'<div class="recommendation-item">{rec}</div>' for rec in context['recommendations'])}
            </div>
        </div>
        
        <footer class="footer">
            <p>Generated by <span class="logo">Aletheia</span> Deepfake Detection Platform</p>
            <p>Report generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </footer>
    </div>
</body>
</html>
"""
        return html
    
    def _generate_pdf_report(
        self,
        data: ReportData,
        options: ReportOptions,
    ) -> tuple[dict[str, Any], BytesIO | None]:
        """Generate PDF format report."""
        # First generate HTML
        _, html_file = self._generate_html_report(data, options)
        html_content = html_file.getvalue().decode("utf-8")
        
        # Convert HTML to PDF using weasyprint if available
        try:
            from weasyprint import HTML
            
            pdf_bytes = HTML(string=html_content).write_pdf()
            file_content = BytesIO(pdf_bytes)
            
        except ImportError:
            # Fallback: return HTML as PDF is not available
            self._logger.warning(
                "WeasyPrint not installed, returning HTML instead of PDF"
            )
            file_content = BytesIO(html_content.encode("utf-8"))
        
        return {}, file_content
    
    # =========================================================================
    # Content Generation
    # =========================================================================
    
    def _generate_summary_text(self, data: ReportData) -> str:
        """Generate human-readable summary."""
        if data.result == "fake":
            verdict = "The video appears to be manipulated or synthetically generated"
            explanation = (
                f"Our analysis detected significant indicators of digital manipulation "
                f"across {data.frames_analyzed} frames with {data.confidence:.1f}% confidence. "
                f"The detected faces ({data.faces_detected}) showed inconsistencies "
                f"characteristic of deepfake generation techniques."
            )
        elif data.result == "real":
            verdict = "The video appears to be authentic"
            explanation = (
                f"Our analysis found no significant indicators of digital manipulation "
                f"across {data.frames_analyzed} frames with {data.confidence:.1f}% confidence. "
                f"The detected faces ({data.faces_detected}) showed consistent natural "
                f"characteristics throughout the video."
            )
        else:
            verdict = "The authenticity of this video could not be determined with certainty"
            explanation = (
                f"Our analysis produced mixed results across {data.frames_analyzed} frames. "
                f"While {data.faces_detected} faces were detected, the evidence for either "
                f"manipulation or authenticity was inconclusive ({data.confidence:.1f}% confidence)."
            )
        
        return f"{verdict}. {explanation}"
    
    def _generate_recommendations(self, data: ReportData) -> list[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        if data.result == "fake":
            recommendations.extend([
                "Do not share this video as authentic content",
                "Consider reporting to the platform if found on social media",
                "Verify the source and original context of the video",
                "Cross-reference with other reliable sources before drawing conclusions",
                "Use reverse image/video search to find the original source",
            ])
        elif data.result == "real":
            recommendations.extend([
                "While our analysis suggests authenticity, always verify with additional sources",
                "Consider the context and source of the video",
                "Be aware that new manipulation techniques may not be detected",
                "For critical decisions, consider consulting additional experts",
            ])
        else:
            recommendations.extend([
                "Seek additional verification before making judgments",
                "Consider having the video analyzed by multiple detection systems",
                "Look for the original source of the video",
                "Examine the video context and metadata",
                "Consult with digital forensics experts for critical use cases",
            ])
        
        # General recommendations
        recommendations.append(
            f"This analysis was performed using {data.model_used} model(s) "
            f"and processed {data.frames_analyzed} frames in {data.processing_time:.1f} seconds"
        )
        
        return recommendations
    
    # =========================================================================
    # Report Management
    # =========================================================================
    
    def get_report(self, report_id: UUID | str) -> "Report":
        """Get report by ID."""
        from detection.models import Report
        
        try:
            return Report.objects.select_related("analysis").get(id=report_id)
        except Report.DoesNotExist:
            raise ProcessingError(
                f"Report not found: {report_id}",
                details={"report_id": str(report_id)},
            )
    
    def get_report_by_token(self, access_token: str) -> "Report":
        """Get report by access token."""
        from detection.models import Report
        
        try:
            report = Report.objects.select_related("analysis").get(
                access_token=access_token
            )
            
            if report.is_expired:
                raise ProcessingError(
                    "Report has expired",
                    details={"report_id": str(report.id)},
                )
            
            return report
            
        except Report.DoesNotExist:
            raise ProcessingError(
                "Invalid or expired report token",
                details={"token": access_token[:8] + "..."},
            )
    
    def record_download(
        self,
        report_id: UUID | str,
        user: Any | None = None,
        ip_address: str | None = None,
        user_agent: str = "",
    ) -> None:
        """Record a report download."""
        from detection.models import Report, ReportDownload
        
        report = self.get_report(report_id)
        report.record_download()
        
        # Create download record
        ReportDownload.objects.create(
            report=report,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else "",
        )
    
    def get_reports_for_analysis(
        self,
        analysis_id: UUID | str,
    ) -> list["Report"]:
        """Get all reports for an analysis."""
        from detection.models import Report
        
        return list(
            Report.objects.filter(analysis_id=analysis_id)
            .order_by("-created_at")
        )
    
    def delete_expired_reports(self) -> int:
        """Delete expired reports."""
        from detection.models import Report
        
        expired = Report.objects.filter(
            expires_at__lt=timezone.now()
        )
        
        count = 0
        for report in expired:
            if report.file_exists:
                report.file.delete(save=False)
            report.delete()
            count += 1
        
        if count > 0:
            self._logger.info(f"Deleted {count} expired reports")
        
        return count
