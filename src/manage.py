"""
Django Management Command Entry Point
"""

import os
import sys
from pathlib import Path


def load_env_file():
    """Load environment variables from .env file."""
    # Get project root (one level up from src/)
    project_root = Path(__file__).resolve().parent.parent
    env_file = project_root / ".env"

    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value


def main():
    """Run administrative tasks."""
    # Load .env file first
    load_env_file()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aletheia.settings")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
