from rest_framework import serializers
from django.contrib.auth import get_user_model


User = get_user_model()

class TelegramAuthSerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField()
    username = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False)
    
    def validate(self, attrs):
        telegram_id = attrs.get('telegram_id')
        user, created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                'username': attrs.get('username') or f"tg_{telegram_id}",
                'first_name': attrs.get('first_name', '')
            }
        )
        attrs['user'] = user
        return attrs