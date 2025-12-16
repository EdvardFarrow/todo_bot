from django.contrib.auth.models import AbstractUser
from apps.core.models import SnowflakeModel

class User(AbstractUser, SnowflakeModel):
    """Custom user with Snowflake ID"""
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"