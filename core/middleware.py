import hashlib
import time

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from .models import SiteSettings
from .auth_throttle import is_authentication_ip_blocked


class LegacyXSSProtectionHeaderMiddleware:
    """Set the legacy browser XSS filter header requested for compatibility."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["X-XSS-Protection"] = "1; mode=block"
        return response


class SensitiveEndpointRateLimitMiddleware:
    """Apply fixed-window request limits to sensitive endpoints by client IP."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if is_authentication_ip_blocked(request):
            response = HttpResponse("Too many failed login attempts. Please try again later.", status=429)
            response["Retry-After"] = str(settings.AUTH_LOCKOUT_DURATION)
            return response

        rule = self._matching_rule(request)
        if rule:
            now = int(time.time())
            window = rule["window"]
            bucket = now // window
            retry_after = window - (now % window)
            client_ip = request.META.get("REMOTE_ADDR", "unknown")
            identity = hashlib.sha256(client_ip.encode("utf-8")).hexdigest()
            key = f"rate-limit:{rule['path']}:{identity}:{bucket}"

            if not cache.add(key, 1, timeout=retry_after):
                try:
                    count = cache.incr(key)
                except ValueError:
                    cache.add(key, 1, timeout=retry_after)
                    count = 1
                if count > rule["limit"]:
                    message = "Too many requests. Please try again later."
                    json_endpoint = request.path_info.startswith("/api/") or request.path_info in ("/newsletter/", "/analytics/track/")
                    response = JsonResponse({"error": message}, status=429) if json_endpoint else HttpResponse(message, status=429)
                    response["Retry-After"] = str(retry_after)
                    return response

        return self.get_response(request)

    @staticmethod
    def _matching_rule(request):
        for rule in settings.RATE_LIMIT_RULES:
            path_matches = (
                request.path_info.startswith(rule["path"])
                if rule.get("prefix")
                else request.path_info == rule["path"]
            )
            if not path_matches or rule["method"] not in ("*", request.method):
                continue
            if rule.get("search_only") and not request.GET.get("q"):
                continue
            return rule
        return None


class MaintenanceModeMiddleware:
    """Keep the public site on an editable maintenance screen while admin stays accessible."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        db_mode = SiteSettings.objects.values_list("maintenance_mode", flat=True).first()
        if getattr(settings, "MAINTENANCE_MODE", False) or db_mode:
            admin_path = settings.ADMIN_URL_PATH
            allowed = request.path.startswith((f"/{admin_path}/", "/static/", "/media/"))
            if not allowed:
                site = SiteSettings.objects.first()
                return render(request, "core/maintenance.html", {"site": site}, status=503)
        return self.get_response(request)
