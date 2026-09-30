import os
import re
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DJANGO_ENV = os.getenv("DJANGO_ENV", "development").strip().lower()
IS_PRODUCTION = DJANGO_ENV in {"production", "prod"}
DEBUG = not IS_PRODUCTION and os.getenv("DEBUG", "False").strip().lower() in {"1", "true", "yes", "on"}
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("DJANGO_SECRET_KEY must be set in the environment before starting Django.")
if IS_PRODUCTION and (len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5):
    raise RuntimeError("In production, DJANGO_SECRET_KEY must be at least 50 characters with at least 5 distinct characters.")

ADMIN_URL_PATH = os.getenv("ADMIN_URL_PATH", "").strip("/")
if IS_PRODUCTION:
    if not re.fullmatch(r"[A-Za-z0-9_-]{24,128}", ADMIN_URL_PATH):
        raise RuntimeError("In production, ADMIN_URL_PATH must be 24-128 URL-safe characters.")
else:
    ADMIN_URL_PATH = (ADMIN_URL_PATH or "secure-console-7f3a91").lower()

RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
ALLOWED_HOSTS = [x.strip() for x in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if x.strip()]
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
CSRF_TRUSTED_ORIGINS = [x.strip() for x in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if x.strip()]
if RENDER_EXTERNAL_HOSTNAME:
    RENDER_ORIGIN = f"https://{RENDER_EXTERNAL_HOSTNAME}"
    if RENDER_ORIGIN not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(RENDER_ORIGIN)
SITE_URL = os.getenv("SITE_URL", "http://127.0.0.1:8000").rstrip("/")
MAINTENANCE_MODE = os.getenv("MAINTENANCE_MODE", "False").lower() == "true"

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "django.contrib.sitemaps", "core.apps.CoreConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "core.middleware.LegacyXSSProtectionHeaderMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "core.middleware.SensitiveEndpointRateLimitMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.MaintenanceModeMiddleware",
]

RATE_LIMIT_RULES = [
    {"path": f"/{ADMIN_URL_PATH}/login/", "method": "POST", "limit": 5, "window": 300},
    {"path": "/contact/", "method": "POST", "limit": 5, "window": 600},
    {"path": "/appointment/", "method": "POST", "limit": 5, "window": 600},
    {"path": "/newsletter/", "method": "POST", "limit": 5, "window": 3600},
    {"path": "/analytics/track/", "method": "GET", "limit": 60, "window": 60},
    {"path": "/api/", "method": "*", "limit": 60, "window": 60, "prefix": True},
    {"path": f"/{ADMIN_URL_PATH}/", "method": "GET", "limit": 30, "window": 60, "search_only": True, "prefix": True},
]
AUTHENTICATION_ENDPOINTS = (f"/{ADMIN_URL_PATH}/login/",)
AUTH_FAILURE_LIMIT = 5
AUTH_FAILURE_WINDOW = 900
AUTH_LOCKOUT_DURATION = 900

ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "core.context_processors.site_settings",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {"default": dj_database_url.config(default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}", conn_health_checks=True)}
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"ai_console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "core.services.ai_service": {
            "handlers": ["ai_console"],
            "level": "INFO",
            "propagate": False,
        }
    },
}

REDIS_URL = os.getenv("REDIS_URL", "").strip()
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 14}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Addis_Ababa"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "website@example.com")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = IS_PRODUCTION or os.getenv("SECURE_SSL_REDIRECT", "False").strip().lower() in {"1", "true", "yes", "on"}
SESSION_COOKIE_SECURE = IS_PRODUCTION or SECURE_SSL_REDIRECT
CSRF_COOKIE_SECURE = IS_PRODUCTION or SECURE_SSL_REDIRECT
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_CSP = {
    "default-src": ["'self'"],
    "base-uri": ["'self'"],
    "object-src": ["'none'"],
    "frame-ancestors": ["'none'"],
    "form-action": ["'self'"],
    "script-src": ["'self'"],
    "script-src-attr": ["'none'"],
    "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
    "font-src": ["'self'", "https://fonts.gstatic.com", "data:"],
    "img-src": ["'self'", "data:", "https:"],
    "connect-src": ["'self'", "https://generativelanguage.googleapis.com"],
    "frame-src": ["'self'", "https://www.youtube.com", "https://www.youtube-nocookie.com"],
}
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000" if IS_PRODUCTION or SECURE_SSL_REDIRECT else "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0 and os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "False").strip().lower() in {"1", "true", "yes", "on"}
SECURE_HSTS_PRELOAD = SECURE_HSTS_SECONDS > 0 and os.getenv("SECURE_HSTS_PRELOAD", "False").strip().lower() in {"1", "true", "yes", "on"}
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024

# Local development uses SQLite; Render production can supply DATABASE_URL for PostgreSQL.
