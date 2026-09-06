"""
Base settings for TechStore project.
Shared across all environments.
"""

from datetime import timedelta
from pathlib import Path

import environ

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Environment
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, []),
)

# Read .env file
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

# Security
SECRET_KEY = env("DJANGO_SECRET_KEY", default="django-insecure-change-me-in-production")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "jazzmin",
]

LOCAL_APPS = [
    "accounts",
    "catalog",
    "inventory",
    "cart",
    "orders",
    "payments",
    "shipping",
    "reviews",
    "promotions",
    "notifications",
    "support",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
# Default to SQLite for development, override with DATABASE_URL for PostgreSQL
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    ),
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "collected_static"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Custom User Model
AUTH_USER_MODEL = "accounts.User"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "login": "10/minute",
        "payment": "20/hour",
    },
}

# JWT Settings
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(env("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=30))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(env("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=7))
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# CORS
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:3000", "http://127.0.0.1:3000"],
)

# DRF Spectacular (API Docs)
SPECTACULAR_SETTINGS = {
    "TITLE": "TechStore API",
    "DESCRIPTION": (
        "TechStore - Online Computer Products Store API\n\n"
        "A complete REST API for an e-commerce platform selling computer hardware, "
        "laptops, peripherals, and accessories. Features include JWT authentication, "
        "product catalog with advanced filtering, shopping cart, order management, "
        "payment gateway integration (Zarinpal), promotions/coupons, product reviews, "
        "and support tickets.\n\n"
        "**Authentication:** Most endpoints require JWT Bearer token. "
        "Register or login to obtain tokens."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "TAGS": [
        {"name": "Auth", "description": "Registration, login, and profile management"},
        {"name": "Addresses", "description": "User shipping addresses"},
        {"name": "Categories", "description": "Product categories (tree structure)"},
        {"name": "Brands", "description": "Product brands"},
        {
            "name": "Products",
            "description": "Product catalog with filtering and search",
        },
        {"name": "Cart", "description": "Shopping cart (guest + authenticated)"},
        {"name": "Cart Items", "description": "Add, update, and remove cart items"},
        {"name": "Cart Coupon", "description": "Apply discount codes to cart"},
        {"name": "Orders", "description": "Order management and checkout"},
        {"name": "Payments", "description": "Payment gateway (Zarinpal)"},
        {"name": "Reviews", "description": "Product reviews and ratings"},
        {"name": "Promotions", "description": "Discount codes and coupons"},
        {"name": "Support", "description": "Support tickets and messaging"},
        {"name": "Health", "description": "System health check"},
    ],
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_TAGS_ALPHA": True,
}

# Payment Gateways
ZARINPAL_MERCHANT_ID = env("ZARINPAL_MERCHANT_ID", default="test-merchant-id")
ZARINPAL_SANDBOX = env.bool("ZARINPAL_SANDBOX", default=True)

# Celery Configuration
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes max per task

# Logging — structured with separate files for payments and orders
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "payments_file": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "payments.log",
            "formatter": "verbose",
        },
        "orders_file": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "orders.log",
            "formatter": "verbose",
        },
        "orders_errors": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "orders_errors.log",
            "level": "ERROR",
            "formatter": "verbose",
        },
        "payments_errors": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "payments_errors.log",
            "level": "ERROR",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "payments": {
            "handlers": ["console", "payments_file", "payments_errors"],
            "level": "INFO",
        },
        "orders": {
            "handlers": ["console", "orders_file", "orders_errors"],
            "level": "INFO",
        },
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
        },
    },
}

# Jazzmin Admin Theme
JAZZMIN_SETTINGS = {
    "site_title": "TechStore Admin",
    "site_header": "TechStore",
    "site_brand": "TechStore",
    "welcome_sign": "Welcome to TechStore Admin Panel",
    "copyright": "TechStore Ltd",
    "search_model": ["accounts.User", "catalog.Product"],
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "API Docs", "url": "/api/docs/", "new_window": True},
    ],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "accounts.User": "fas fa-user-circle",
        "catalog.Category": "fas fa-tags",
        "catalog.Brand": "fas fa-award",
        "catalog.Product": "fas fa-box",
        "inventory.StockItem": "fas fa-warehouse",
        "cart.Cart": "fas fa-shopping-cart",
        "orders.Order": "fas fa-receipt",
        "payments.Payment": "fas fa-credit-card",
        "reviews.Review": "fas fa-star",
        "promotions.Coupon": "fas fa-percent",
        "support.Ticket": "fas fa-headset",
    },
}
