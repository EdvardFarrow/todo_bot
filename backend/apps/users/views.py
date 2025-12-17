from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .serializers import TelegramAuthSerializer, UserProfileSerializer
from rest_framework import viewsets, permissions
from django.contrib.auth import get_user_model


User = get_user_model()


class TelegramAuthView(APIView):
    """
    Login or Register via Telegram ID.
    """
    permission_classes = [] 

    def post(self, request):
        serializer = TelegramAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "user_id": str(user.id) # Snowflake string
        })
        

class UserViewSet(viewsets.ModelViewSet):
    """
    API for retrieving and updating user profile (language, timezone).
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)
    
    def get_object(self):
        return super().get_object()