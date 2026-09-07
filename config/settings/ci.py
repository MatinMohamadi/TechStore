"""
CI settings for TechStore project.
Used by GitHub Actions workflow.
"""

from .base import *  # noqa: F401,F403

DEBUG = True

# CI always uses SQLite (no PostgreSQL dependency for unit tests)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.ci.sqlite3",
    }
}

# Use in-memory email backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Celery: run tasks eagerly (synchronously) in CI
CELERY_TASK_ALWAYS_EAGER = True

# CORS: allow all in CI
CORS_ALLOW_ALL_ORIGINS = True

# No SSL redirect in CI
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = None

# Speed up password hashing in tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable throttling in CI tests
REST_FRAMEWORK = {
    **globals().get("REST_FRAMEWORK", {}),
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "10000/hour",
        "user": "10000/hour",
        "login": "10000/minute",
        "payment": "10000/hour",
    },
}
