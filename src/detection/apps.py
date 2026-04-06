"""
Detection Application Configuration
"""

from django.apps import AppConfig


class DetectionConfig(AppConfig):
    """Django app configuration for detection module."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "detection"
    verbose_name = "Deepfake Detection"
    
    def ready(self) -> None:
        """
        Initialize application on Django startup.
        
        - Register signal handlers
        - Initialize ML models (lazy loading)
        - Set up logging
        """
        # Import signals to register handlers
        try:
            from detection import signals  # noqa: F401
        except ImportError:
            pass
