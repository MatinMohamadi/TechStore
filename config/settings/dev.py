"""
Development settings for TechStore project.
"""
from .base import *  # noqa: F401,F403

DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ["*"]

# CORS - allow all in development
CORS_ALLOW_ALL_ORIGINS = True

# Simplified error pages
DEBUG_PROPAGATE_EXCEPTIONS = True

# Email backend - console for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
