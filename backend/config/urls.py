from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/v1/', include('apps.tasks.urls')),
    path('api/v1/users/', include('apps.users.urls')),
]
