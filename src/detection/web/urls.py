"""
Detection web URLs (for serving frontend).
"""

from django.urls import path
from django.views.generic import TemplateView

app_name = "web"

urlpatterns = [
    # Serve React frontend (in production, use proper static file serving)
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
]
