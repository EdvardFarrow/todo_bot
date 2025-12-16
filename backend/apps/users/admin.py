from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.users.models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Admin configuration for Custom User model.
    """
    list_display = ("username", "email", "id", "is_staff")
    ordering = ("date_joined",)
    
    fieldsets = UserAdmin.fieldsets