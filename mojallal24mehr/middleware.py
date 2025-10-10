import time
import sys
import os
from typing import Optional

from django.views import debug as django_debug

try:
    from django.utils.deprecation import MiddlewareMixin  # for compatibility
except Exception:  # pragma: no cover
    MiddlewareMixin = object

# Force debug pages regardless of settings and DB (can be disabled by setting FORCE_DEBUG=0)
_FORCE_DEBUG = os.getenv('FORCE_DEBUG', '1').lower() in ('1', 'true', 'yes', 'on')

# Lightweight in-process cache to avoid DB hit every request
_DEBUG_CACHE = {
    'value': None,      # type: Optional[int]
    'ts': 0.0,         # last fetch timestamp
}
_CACHE_TTL = 5.0  # seconds


def _get_debug_mode_from_db():
    """Fetch current debug_mode from active MasterInfo with short caching."""
    now = time.time()
    if _DEBUG_CACHE['value'] is not None and (now - _DEBUG_CACHE['ts'] < _CACHE_TTL):
        return _DEBUG_CACHE['value']

    try:
        from dashboard.models import MasterInfo  # imported lazily to avoid app registry issues
        qs = MasterInfo.objects.filter(is_active=True)
        mode = qs.values_list('debug_mode', flat=True).last()
        if mode is None:
            mode = 3
    except Exception:
        # Any DB/app errors -> default OFF
        mode = 3
    _DEBUG_CACHE['value'] = mode
    _DEBUG_CACHE['ts'] = now
    return mode


class DebugModeMiddleware(MiddlewareMixin):
    """
    Per-request debug behavior controller.

    Modes (MasterInfo.debug_mode):
      1 -> Debug ON for everyone (return technical_500_response on exceptions)
      2 -> Debug ON for admins only (superusers)
      3 -> Debug OFF (use normal handlers)

    This does not toggle settings.DEBUG; it only affects exception rendering,
    so static/media and security remain production-like.
    """

    def process_exception(self, request, exception):
        # If force flag is active, always show technical debug page
        if _FORCE_DEBUG:
            exc_info = sys.exc_info()
            try:
                return django_debug.technical_500_response(request, *exc_info)
            finally:
                del exc_info

        try:
            mode = _get_debug_mode_from_db()
        except Exception:
            # If DB is unavailable, fall back to production behavior
            return None

        show_debug = False
        if mode == 1:
            show_debug = True
        elif mode == 2:
            user = getattr(request, 'user', None)
            if getattr(user, 'is_authenticated', False) and getattr(user, 'is_superuser', False):
                show_debug = True

        if not show_debug:
            return None

        exc_info = sys.exc_info()
        try:
            return django_debug.technical_500_response(request, *exc_info)
        finally:
            # help GC
            del exc_info
