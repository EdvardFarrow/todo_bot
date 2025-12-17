from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TelegramAuthView, UserViewSet


router = DefaultRouter()
router.register(r'profile', UserViewSet, basename='user_profile')

urlpatterns = [
    path('auth/telegram/', TelegramAuthView.as_view(), name='telegram_auth'),
    path('', include(router.urls)),
]