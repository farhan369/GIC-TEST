"""
URL configuration for gic_test project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from common.views import TaskStatusView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('tasks/<str:task_id>/status/', TaskStatusView.as_view(), name='task_status'),
    path('v1/users/', include('v1.users.urls')),
    path('rate-limiter/', include('middleware.rate_limiter.urls')),
]
