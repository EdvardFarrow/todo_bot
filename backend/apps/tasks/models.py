from django.db import models
from django.conf import settings
from apps.core.models import SnowflakeModel

class Category(SnowflakeModel):
    name = models.CharField("Name", max_length=100)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="categories",
        verbose_name="Owner"
    )

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        unique_together = [('name', 'user')] 

    def __str__(self) -> str:
        return self.name

class Task(SnowflakeModel):
    title = models.CharField(verbose_name = "Title", max_length=255)
    description = models.TextField(verbose_name = "Description", blank=True)
    deadline = models.DateTimeField(verbose_name = "Deadline", null=True, blank=True)
    
    is_completed = models.BooleanField(verbose_name = "Completed", default=False)
    is_notified = models.BooleanField(default=False, verbose_name="Deadline Missed Sent")
    is_pre_notified = models.BooleanField(default=False, verbose_name="10-min Warning Sent")
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks"
    )

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title