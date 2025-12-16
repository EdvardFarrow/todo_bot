from django.db import models
from . import snowflake

def next_snowflake_id() -> int:
    """Wrapper for default callable"""
    if snowflake.generator is None:
        return snowflake.SnowflakeGenerator(1).next_id()
    return snowflake.generator.next_id()

class SnowflakeModel(models.Model):
    id = models.BigIntegerField(
        primary_key=True, 
        default=next_snowflake_id, 
        editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True