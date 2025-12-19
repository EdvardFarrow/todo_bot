from django.contrib import admin

from apps.tasks.models import Category, Task

try:
    admin.site.unregister(Task)
except admin.sites.NotRegistered:  # type: ignore
    pass

try:
    admin.site.unregister(Category)
except admin.sites.NotRegistered:  # type: ignore
    pass


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "category", "deadline", "is_completed")
    list_filter = ("is_completed", "created_at")
    search_fields = ("title", "id")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user")
