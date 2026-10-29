import hashlib

from django.core.cache import cache

from .models import LocationView

VIEW_TTL = 60 * 60


def get_viewer_key(request):
    if request.user.is_authenticated:
        return f"user:{request.user.pk}"

    ip = request.META.get("REMOTE_ADDR", "")
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    viewer_hash = hashlib.sha256(f"{ip}|{user_agent}".encode()).hexdigest()[:32]
    return f"anon:{viewer_hash}"


def register_view(location, request):
    viewer_key = get_viewer_key(request)
    cache_key = f"location_view:{location.pk}:{viewer_key}"
    if not cache.add(cache_key, 1, timeout=VIEW_TTL):
        return False

    user = request.user if request.user.is_authenticated else None
    LocationView.objects.create(location=location, user=user, viewer_key=viewer_key)
    return True
