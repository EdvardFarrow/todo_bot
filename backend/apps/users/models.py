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
    
    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'English'),
    ]
    language = models.CharField(
        "Language", 
        max_length=10, 
        choices=LANGUAGE_CHOICES, 
        default='en' 
    )
    timezone = models.CharField(
        "Timezone", 
        max_length=50, 
        default='UTC'
    )
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"