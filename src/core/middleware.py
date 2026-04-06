"""
Core Middleware

Custom middleware for the Aletheia platform.
"""

from __future__ import annotations

from django.conf import settings
from django.http import HttpRequest, HttpResponse


class HSTSResetMiddleware:
    """
    Middleware that sends 'Strict-Transport-Security: max-age=0' header
    to actively clear any cached HSTS policy from the browser.

    This is critical for local development: if HSTS was previously cached
    (e.g. from a production settings run), the browser will force HTTPS
    for localhost indefinitely. Sending max-age=0 instructs the browser
    to stop enforcing HTTPS.

    This middleware only activates when SECURE_HSTS_SECONDS is 0 and
    the request is served over HTTPS (browsers only process HSTS headers
    on secure connections).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        # Only send HSTS reset when HSTS is disabled in settings
        hsts_seconds = getattr(settings, "SECURE_HSTS_SECONDS", 0)
        if hsts_seconds == 0:
            # Send max-age=0 to clear any previously cached HSTS policy.
            # This only works over HTTPS connections (browsers ignore HSTS
            # headers on plain HTTP), so it pairs with runsslserver.
            response["Strict-Transport-Security"] = "max-age=0"

        return response
