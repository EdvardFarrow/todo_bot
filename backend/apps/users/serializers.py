from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class TelegramAuthSerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField()
    username = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False)
    language_code = serializers.CharField(required=False)

    def validate(self, attrs):
        telegram_id = attrs.get("telegram_id")
        incoming_lang = attrs.get("language_code", "en")

        if incoming_lang in ["ru", "be", "uk", "kz"]:
            final_lang = "ru"
        else:
            final_lang = "en"

        user, created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                "username": attrs.get("username") or f"tg_{telegram_id}",
                "first_name": attrs.get("first_name", ""),
                "language": final_lang,
                "timezone": "UTC",
            },
        )
        attrs["user"] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "language", "timezone"]
        read_only_fields = ["id", "username"]
