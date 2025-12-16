from django.contrib import admin
from apps.tasks.models import Task, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "created_at")
    search_fields = ("name", "user__username")

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "category", "deadline", "is_completed")
    list_filter = ("is_completed", "created_at", "deadline")
    search_fields = ("title", "description", "user__username")