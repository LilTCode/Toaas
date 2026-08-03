from django.urls import path
from .views import ChatConversationListView, ChatConversationCreateView, ChatMessageCreateView

urlpatterns = [
    path("conversations/", ChatConversationListView.as_view(), name="conversation-list"),
    path("conversations/create/", ChatConversationCreateView.as_view(), name="conversation-create"),
    path("conversations/<int:conversation_id>/messages/", ChatMessageCreateView.as_view(), name="conversation-message-create"),
]
