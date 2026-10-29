import hashlib
from urllib.parse import urlencode

from django.core.cache import cache

LIST_TTL = 60 * 5
VERSION_KEY = "locations:list:version"


def list_cache_key(request):
    version = cache.get_or_set(VERSION_KEY, 1, timeout=None)
    params = urlencode(sorted(request.query_params.lists()), doseq=True)
    params_hash = hashlib.sha256(params.encode()).hexdigest()
    return f"locations:list:v{version}:{params_hash}"


def invalidate_locations_list():
    try:
        cache.incr(VERSION_KEY)
    except ValueError:
        cache.set(VERSION_KEY, 1, timeout=None)
