from django.http import JsonResponse
import requests
from django.views.decorators.csrf import csrf_exempt
import json
import time
from django.core.cache import cache

@csrf_exempt
def test_rate_limiter(request, num_requests):
    """
    Test endpoint for rate limiter that accepts number of requests to make
    GET /rate-limiter/test/100/
    Where 100 is the number of requests you want to make
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method allowed'}, status=405)
    
    try:
        num_requests = int(num_requests)
    except ValueError:
        return JsonResponse({'error': 'Number of requests must be a valid integer'}, status=400)

    if num_requests <= 0:
        return JsonResponse({'error': 'Number of requests must be a positive integer'}, status=400)

    base_url = request.build_absolute_uri('/rate-limiter/ping/')
    results = []

    def make_request():
        response = requests.get(base_url)
        return {
            'status_code': response.status_code,
            'headers': {
                'X-RateLimit-Limit': response.headers.get('X-RateLimit-Limit'),
                'X-RateLimit-Remaining': response.headers.get('X-RateLimit-Remaining'),
                'X-RateLimit-Reset': response.headers.get('X-RateLimit-Reset')
            }
        }

    # Make sequential requests
    for _ in range(num_requests):
        results.append(make_request())
        time.sleep(0.1)  # Small delay to prevent overwhelming the server

    # Analyze results
    success_count = sum(1 for r in results if r['status_code'] == 200)
    rate_limited_count = sum(1 for r in results if r['status_code'] == 429)

    return JsonResponse({
        'total_requests': num_requests,
        'successful_requests': success_count,
        'rate_limited_requests': rate_limited_count,
        'results': results
    })

def ping(request):
    """
    Simple ping endpoint that will be rate limited
    """
    return JsonResponse({'message': 'pong'})

@csrf_exempt
def clear_cache(request):
    """
    Clear all rate limiter cache entries
    DELETE /rate-limiter/clear/
    """
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Only DELETE method allowed'}, status=405)
    
    # Get all cache keys that start with 'rate_limit:'
    keys = cache.keys('rate_limit:*')
    if keys:
        cache.delete_many(keys)
    
    return JsonResponse({
        'message': 'Rate limiter cache cleared successfully',
        'keys_cleared': len(keys) if keys else 0
    }) 