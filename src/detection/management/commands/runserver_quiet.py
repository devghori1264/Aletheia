"""
Custom runserver command that suppresses HTTPS error noise.

These errors occur when external bots/scanners try to connect via HTTPS,
but Django's runserver only supports HTTP. They are harmless and don't
affect the application functionality.

Usage:
    python manage.py runserver_quiet 0.0.0.0:8000
"""

import logging
from django.core.management.commands.runserver import Command as RunserverCommand


class HTTPSErrorFilter(logging.Filter):
    """Filter to suppress HTTPS-related error messages"""
    
    def filter(self, record):
        # Suppress "accessing the development server over HTTPS" messages
        message = str(record.getMessage())
        if "HTTPS, but it only supports HTTP" in message:
            return False
        if "Bad request" in message and "\\x16\\x03" in message:
            return False
        return True


class Command(RunserverCommand):
    help = "Starts a lightweight Web server for development (with HTTPS errors suppressed)"

    def handle(self, *args, **options):
        # Add filter to suppress HTTPS errors
        logger = logging.getLogger('django.server')
        logger.addFilter(HTTPSErrorFilter())
        
        # Also filter basehttp logger (for development mode)
        basehttp_logger = logging.getLogger('basehttp')
        basehttp_logger.addFilter(HTTPSErrorFilter())
        
        # Call the parent command
        super().handle(*args, **options)
