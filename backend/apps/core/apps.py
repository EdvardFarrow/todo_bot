from django.apps import AppConfig
from django.conf import settings
from . import snowflake

class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"

    def ready(self) -> None:
        machine_id = getattr(settings, "SNOWFLAKE_MACHINE_ID", 1)
        snowflake.generator = snowflake.SnowflakeGenerator(machine_id=machine_id)