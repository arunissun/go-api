"""
Minimal Django settings for the trigger-builder standalone Cloud Run service.

No database. No Celery. No storage backends.
Stateless API: receives form data, builds deterministic draft, calls Gemini, returns result.
"""

import os
from pathlib import Path

from corsheaders.defaults import default_headers
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "").strip()
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be provided.")

DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "corsheaders",
    "rest_framework",
    "trigger_builder",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "trigger_builder_standalone.urls"

WSGI_APPLICATION = "trigger_builder_standalone.wsgi.application"

# No database — stateless API
DATABASES = {}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# CORS — allow the frontend Cloud Run URL (set at deploy time)
_default_origins = ",".join(
    [
        "https://trigger-builder-frontend-miiriseyfa-uc.a.run.app",
        "http://localhost:3101",
        "http://localhost:4173",
        "http://localhost:5173",
    ]
)
_raw_origins = os.environ.get("CORS_ALLOWED_ORIGINS", _default_origins)
CORS_ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_HEADERS = (*default_headers, "x-prototype-access-code")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    # No auth app in INSTALLED_APPS — disable the AnonymousUser model entirely.
    "UNAUTHENTICATED_USER": None,
    # Browsers send Accept: text/html which triggers BrowsableAPIRenderer; that renderer
    # requires django.contrib.auth (not in INSTALLED_APPS) and raises a 500. Force JSON only.
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

# Path to the implementation_inputs directory.
# Override with IMPLEMENTATION_INPUTS_DIR env var in Docker / Cloud Run.
IMPLEMENTATION_INPUTS_DIR = os.environ.get(
    "IMPLEMENTATION_INPUTS_DIR",
    str(BASE_DIR.parent.parent / "implementation_inputs"),
)

# Vertex AI
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "eap-form-prototype")
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
GEMINI_MODEL_ID = os.environ.get("GEMINI_MODEL_ID", "gemini-3.5-flash")
GEMINI_PROMPT_VERSION = os.environ.get("GEMINI_PROMPT_VERSION", "phase1-v1")
GEMINI_REQUEST_TIMEOUT_SECONDS = int(
    os.environ.get("GEMINI_REQUEST_TIMEOUT_SECONDS", "150")
)

PROTOTYPE_ACCESS_REQUIRED = os.environ.get("PROTOTYPE_ACCESS_REQUIRED", "false").lower() == "true"
PROTOTYPE_ACCESS_CODE = os.environ.get("PROTOTYPE_ACCESS_CODE", "")
if PROTOTYPE_ACCESS_REQUIRED and not PROTOTYPE_ACCESS_CODE:
    raise ImproperlyConfigured(
        "PROTOTYPE_ACCESS_CODE must be provided when PROTOTYPE_ACCESS_REQUIRED=true."
    )

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
