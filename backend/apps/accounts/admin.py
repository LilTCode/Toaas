from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Role and Verification", {"fields": ("role", "is_email_verified", "otp_code", "otp_expires_at")}),
    )
    list_display = ["username", "email", "role", "is_email_verified", "is_staff"]
    search_fields = ["username", "email"]
