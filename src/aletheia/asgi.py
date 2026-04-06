"""
ASGI Configuration for Aletheia

This module contains the ASGI application used for async-capable deployments
including WebSocket support for real-time updates during video analysis.

ASGI enables:
    - HTTP/2 and WebSocket protocols
    - Real-time analysis progress updates
    - Efficient handling of long-running requests

Production Deployment:
    uvicorn aletheia.asgi:application --host 0.0.0.0 --port 8000

For more information on ASGI, see:
    https://docs.djangoproject.com/en/stable/howto/deployment/asgi/
"""

from __future__ import annotations

import os

from django.core.asgi import get_asgi_application

# Set default settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aletheia.settings")

# Initialize Django ASGI application early to ensure AppRegistry is populated
django_asgi_app = get_asgi_application()

# Import after Django setup to avoid AppRegistryNotReady
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.auth import AuthMiddlewareStack  # noqa: E402


# Define WebSocket URL patterns
websocket_urlpatterns = [
    # WebSocket routes will be added here
    # path("ws/analysis/<uuid:analysis_id>/", AnalysisProgressConsumer.as_asgi()),
]

# ASGI application with protocol routing
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    # "websocket": AuthMiddlewareStack(
    #     URLRouter(websocket_urlpatterns)
    # ),
})
