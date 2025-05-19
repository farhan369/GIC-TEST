from django.test import RequestFactory, TestCase
from django.http import HttpResponse
from django.core.cache import cache
from unittest.mock import patch

from .rate_limiter import RateLimitMiddleware
from django.conf import settings

# Constants for rate limiting
RATE_LIMIT_MAX_REQUESTS = getattr(settings, 'RATE_LIMIT_MAX_REQUESTS', 100)
RATE_LIMIT_WINDOW_SECONDS = getattr(settings, 'RATE_LIMIT_WINDOW_SECONDS', 300)

class RateLimitMiddlewareTests(TestCase):
    """
    Unit tests for the RateLimitMiddleware.
    """

    def setUp(self):
        """
        Set up the test environment before each test method.
        """
        self.factory = RequestFactory()
        self.middleware = RateLimitMiddleware(lambda req: HttpResponse("OK"))
        cache.clear()

    @patch('time.time', return_value=1000)
    def test_first_request_allowed(self, mock_time):
        """
        Test that the first request from an IP is allowed.
        """
        request = self.factory.get('/test/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        response = self.middleware.process_request(request)

        self.assertIsNone(response)
        self.assertEqual(cache.get('rate_limit:192.168.1.1'), [1000])
        self.assertEqual(request._rate_limit_remaining, RATE_LIMIT_MAX_REQUESTS - 1)

    @patch('time.time')
    def test_multiple_requests_within_limit_allowed(self, mock_time):
        """
        Test that multiple requests within the limit are allowed and headers are set.
        """
        ip = '192.168.1.2'
        timestamps = [1000 + i for i in range(RATE_LIMIT_MAX_REQUESTS - 1)]
        cache.set(f'rate_limit:{ip}', timestamps)

        mock_time.return_value = 1000 + RATE_LIMIT_MAX_REQUESTS
        request = self.factory.get('/test/')
        request.META['REMOTE_ADDR'] = ip
        response = self.middleware.process_request(request)

        self.assertIsNone(response)
        self.assertEqual(len(cache.get(f'rate_limit:{ip}')), RATE_LIMIT_MAX_REQUESTS)
        self.assertEqual(request._rate_limit_remaining, 0)

        mock_response = HttpResponse("OK")
        processed_response = self.middleware.process_response(request, mock_response)
        self.assertEqual(processed_response.status_code, 200)
        self.assertEqual(processed_response['X-RateLimit-Limit'], str(RATE_LIMIT_MAX_REQUESTS))
        self.assertEqual(processed_response['X-RateLimit-Remaining'], '0')


    @patch('time.time')
    def test_request_exceeding_limit_blocked(self, mock_time):
        """
        Test that a request exceeding the limit is blocked with a 429 response.
        """
        ip = '192.168.1.3'
        timestamps = [1000 + i for i in range(RATE_LIMIT_MAX_REQUESTS)]
        cache.set(f'rate_limit:{ip}', timestamps)

        mock_time.return_value = 1000 + RATE_LIMIT_MAX_REQUESTS + 1
        request = self.factory.get('/test/')
        request.META['REMOTE_ADDR'] = ip
        response = self.middleware.process_request(request)

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response['X-RateLimit-Limit'], str(RATE_LIMIT_MAX_REQUESTS))
        self.assertEqual(response['X-RateLimit-Remaining'], '0')
        self.assertEqual(len(cache.get(f'rate_limit:{ip}')), RATE_LIMIT_MAX_REQUESTS + 1)


    @patch('time.time')
    def test_old_timestamps_are_removed(self, mock_time):
        """
        Test that timestamps older than the window are removed.
        """
        ip = '192.168.1.4'
        timestamps = [
            1000 - (RATE_LIMIT_WINDOW_SECONDS + 10),
            1000 - (RATE_LIMIT_WINDOW_SECONDS + 5),
            1000 - 50,
            1000 - 30,
            1000 - 10,
        ]
        cache.set(f'rate_limit:{ip}', timestamps)

        mock_time.return_value = 1000
        request = self.factory.get('/test/')
        request.META['REMOTE_ADDR'] = ip
        response = self.middleware.process_request(request)

        self.assertIsNone(response)
        updated_timestamps = cache.get(f'rate_limit:{ip}')
        self.assertEqual(len(updated_timestamps), 4)
        self.assertNotIn(1000 - (RATE_LIMIT_WINDOW_SECONDS + 10), updated_timestamps)
        self.assertNotIn(1000 - (RATE_LIMIT_WINDOW_SECONDS + 5), updated_timestamps)
        self.assertIn(1000 - 50, updated_timestamps)
        self.assertIn(1000 - 30, updated_timestamps)
        self.assertIn(1000 - 10, updated_timestamps)
        self.assertIn(1000, updated_timestamps)
        self.assertEqual(request._rate_limit_remaining, RATE_LIMIT_MAX_REQUESTS - 4)


