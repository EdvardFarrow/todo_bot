from django.contrib import admin
from apps.tasks.models import Task, Category


try:
    admin.site.unregister(Task)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(Category)
except admin.sites.NotRegistered:
    pass


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'category', 'deadline', 'is_completed')
    list_filter = ('is_completed', 'created_at')
    search_fields = ('title', 'id') 

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user') 