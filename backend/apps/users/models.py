from django.db import models
from django.contrib.auth.models import AbstractUser
from apps.core.models import SnowflakeModel

class User(AbstractUser, SnowflakeModel):
    """Custom user with Snowflake ID"""
    telegram_id = models.BigIntegerField(
        "Telegram ID", 
        unique=True, 
        null=True, 
        blank=True,
        db_index=True
    )
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"