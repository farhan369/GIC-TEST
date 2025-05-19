import time

from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse


class RateLimitMiddleware(MiddlewareMixin):
    """
    Custom middleware to implement IP-based request rate limiting.

    Uses Django's cache framework to store request timestamps for each IP.
    Blocks requests if an IP exceeds RATE_LIMIT_MAX_REQUESTS within a
    rolling RATE_LIMIT_WINDOW_SECONDS window.
    """
    RATE_LIMIT_MAX_REQUESTS = getattr(settings, 'RATE_LIMIT_MAX_REQUESTS', 100)
    RATE_LIMIT_WINDOW_SECONDS = getattr(settings, 'RATE_LIMIT_WINDOW_SECONDS', 300)

    def process_request(self, request):
        """
        Processes the incoming request to check for rate limiting.
        """
        ip_address = request.META.get('REMOTE_ADDR')
        if not ip_address:
            return None

        cache_key = f'rate_limit:{ip_address}'

        request_timestamps = cache.get(cache_key, [])
        current_time = time.time()
        request_timestamps = [
            timestamp for timestamp in request_timestamps
            if timestamp > current_time - self.RATE_LIMIT_WINDOW_SECONDS
        ]

        request_timestamps.append(current_time)

        cache.set(cache_key, request_timestamps, timeout=self.RATE_LIMIT_WINDOW_SECONDS + 60)

        remaining_requests = self.RATE_LIMIT_MAX_REQUESTS - len(request_timestamps)

        if len(request_timestamps) > self.RATE_LIMIT_MAX_REQUESTS:
            response = HttpResponse("Too Many Requests", status=429)
            response['X-RateLimit-Limit'] = self.RATE_LIMIT_MAX_REQUESTS
            response['X-RateLimit-Remaining'] = 0
            return response

        request._rate_limit_remaining = remaining_requests

        return None

    def process_response(self, request, response):
        """
        Adds rate limit headers to the response for successful requests.
        """

        if hasattr(request, '_rate_limit_remaining'):
            response['X-RateLimit-Limit'] =  self.RATE_LIMIT_MAX_REQUESTS
            response['X-RateLimit-Remaining'] = request._rate_limit_remaining

        return response

