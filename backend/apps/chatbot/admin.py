from django.contrib import admin
from .models import ChatConversation, ChatMessage


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ["student", "created_at", "updated_at"]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ["conversation", "sender_role", "created_at"]
    search_fields = ["content", "conversation__student__email"]
