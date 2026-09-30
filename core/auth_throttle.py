import hashlib

from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.core.cache import cache
from django.dispatch import receiver


def _cache_keys(request):
    if request is None or request.path_info not in settings.AUTHENTICATION_ENDPOINTS:
        return None
    client_ip = request.META.get("REMOTE_ADDR", "unknown")
    identity = hashlib.sha256(client_ip.encode("utf-8")).hexdigest()
    return f"auth-failures:{identity}", f"auth-lockout:{identity}"


def is_authentication_ip_blocked(request):
    keys = _cache_keys(request)
    return bool(keys and cache.get(keys[1], False))


@receiver(user_login_failed, dispatch_uid="core.record_failed_login")
def record_failed_login(sender, credentials, request=None, **kwargs):
    keys = _cache_keys(request)
    if not keys:
        return

    failure_key, lockout_key = keys
    if cache.add(failure_key, 1, timeout=settings.AUTH_FAILURE_WINDOW):
        failures = 1
    else:
        try:
            failures = cache.incr(failure_key)
        except ValueError:
            cache.add(failure_key, 1, timeout=settings.AUTH_FAILURE_WINDOW)
            failures = 1

    if failures >= settings.AUTH_FAILURE_LIMIT:
        cache.set(lockout_key, True, timeout=settings.AUTH_LOCKOUT_DURATION)


@receiver(user_logged_in, dispatch_uid="core.clear_failed_login_count")
def clear_failed_login_count(sender, request=None, **kwargs):
    keys = _cache_keys(request)
    if keys:
        cache.delete_many(keys)