"""
Custom Django management command: runsslserver

Runs Django's development server with HTTPS/SSL support using a
self-signed certificate. This is useful when browsers enforce HSTS
or HTTPS-First mode for localhost.

Usage:
    python manage.py runsslserver 0.0.0.0:8000
    python manage.py runsslserver --certificate /path/to/cert.pem --key /path/to/key.pem

The command auto-generates a self-signed certificate if none is provided.
"""

from __future__ import annotations

import os
import ssl
import subprocess
import sys
from pathlib import Path

from django.core.management.commands.runserver import Command as BaseRunserverCommand
from django.core.servers.basehttp import WSGIServer


class SecureWSGIServer(WSGIServer):
    """WSGIServer subclass that wraps the listening socket with TLS/SSL."""

    # Class-level attributes set by the management command before server starts
    certificate: str | None = None
    key: str | None = None

    def server_bind(self):
        """Bind the server socket and wrap it with SSL."""
        super().server_bind()
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(
            certfile=self.certificate,
            keyfile=self.key,
        )
        # Disable hostname checking for self-signed certs
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        self.socket = context.wrap_socket(
            self.socket,
            server_side=True,
        )


class Command(BaseRunserverCommand):
    """Runs the Django development server with HTTPS/SSL support."""

    help = (
        "Runs the development server with HTTPS. Auto-generates a self-signed "
        "certificate if none exists. Use this when your browser forces HTTPS "
        "for localhost (due to HSTS caching or HTTPS-First mode)."
    )
    protocol = "https"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--certificate",
            dest="certificate",
            default=None,
            help="Path to the SSL certificate file (PEM format). "
            "Auto-generated if not provided.",
        )
        parser.add_argument(
            "--key",
            dest="key",
            default=None,
            help="Path to the SSL private key file (PEM format). "
            "Auto-generated if not provided.",
        )

    def handle(self, *args, **options):
        # Determine certificate paths
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        ssl_dir = project_root / ".ssl"

        cert_file = options.get("certificate") or str(ssl_dir / "localhost.pem")
        key_file = options.get("key") or str(ssl_dir / "localhost-key.pem")

        # Auto-generate self-signed certificate if needed
        if not os.path.exists(cert_file) or not os.path.exists(key_file):
            self._generate_self_signed_cert(ssl_dir, cert_file, key_file)

        # Configure the secure server
        SecureWSGIServer.certificate = cert_file
        SecureWSGIServer.key = key_file
        self.server_cls = SecureWSGIServer

        self.stdout.write(
            self.style.SUCCESS(
                "\n"
                "╔══════════════════════════════════════════════════════════════╗\n"
                "║  🔒 HTTPS Development Server                               ║\n"
                f"║  Certificate: {Path(cert_file).name:<45} ║\n"
                f"║  Key:         {Path(key_file).name:<45} ║\n"
                "║                                                            ║\n"
                "║  ⚠️  Self-signed cert — accept the browser warning once     ║\n"
                "║  This will also clear cached HSTS for localhost             ║\n"
                "╚══════════════════════════════════════════════════════════════╝\n"
            )
        )

        super().handle(*args, **options)

    def _generate_self_signed_cert(self, ssl_dir: Path, cert_file: str, key_file: str):
        """Generate a self-signed certificate using openssl."""
        ssl_dir.mkdir(parents=True, exist_ok=True)

        self.stdout.write("Generating self-signed SSL certificate...")

        try:
            subprocess.run(
                [
                    "openssl",
                    "req",
                    "-x509",
                    "-newkey",
                    "rsa:2048",
                    "-keyout",
                    key_file,
                    "-out",
                    cert_file,
                    "-days",
                    "365",
                    "-nodes",
                    "-subj",
                    "/CN=localhost",
                    "-addext",
                    "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:0.0.0.0",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.stdout.write(
                self.style.SUCCESS(f"✅ Certificate generated at {ssl_dir}/")
            )
        except FileNotFoundError:
            self.stderr.write(
                self.style.ERROR(
                    "ERROR: 'openssl' command not found.\n"
                    "Install OpenSSL or provide certificate files manually:\n"
                    "  brew install openssl   # macOS\n"
                    "  apt install openssl    # Ubuntu/Debian"
                )
            )
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            self.stderr.write(
                self.style.ERROR(
                    f"ERROR: Failed to generate certificate:\n{e.stderr}"
                )
            )
            sys.exit(1)
