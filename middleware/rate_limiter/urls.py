from django.urls import path
from .views import test_rate_limiter, ping, clear_cache

app_name = 'rate_limiter'

urlpatterns = [
    path('test/<int:num_requests>/', test_rate_limiter, name='test_rate_limiter'),
    path('ping/', ping, name='ping'),
    path('clear/', clear_cache, name='clear_cache'),
] 