from django.db import models
from django.conf import settings


class ChatConversation(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_conversations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation({self.student.email}, {self.created_at:%Y-%m-%d})"


class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ("student", "Student"),
        ("advisor", "Advisor"),
        ("system", "System"),
    ]
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name="messages")
    sender_role = models.CharField(max_length=32, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender_role}: {self.content[:50]}"
