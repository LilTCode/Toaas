from django.urls import path
from .views import (
    CognitiveProfileView, GenerateRecommendationView, RecommendationListView,
    RecommendationAcknowledgeView, ActivityListView, AdvisorMessageListCreateView,
    AdvisorMessageReplyView, StaffMessageListView, StaffMessageReplyView,
    AdvisorStudentListView, AdvisorStudentDetailView,
    StaffSendMessageView, AdvisorRecommendationReviewView,
    StaffContactAdminView, StaffMyMessagesView,
)

urlpatterns = [
    path("profile/", CognitiveProfileView.as_view(), name="cognitive-profile"),
    path("recommendations/", RecommendationListView.as_view(), name="recommendation-list"),
    path("recommendations/generate/", GenerateRecommendationView.as_view(), name="recommendation-generate"),
    path("recommendations/<int:recommendation_id>/acknowledge/", RecommendationAcknowledgeView.as_view(), name="recommendation-acknowledge"),
    path("students/<int:student_id>/review-recommendation/", AdvisorRecommendationReviewView.as_view(), name="advisor-review-recommendation"),
    path("activity/", ActivityListView.as_view(), name="activity-list"),
    # Student messaging
    path("messages/", AdvisorMessageListCreateView.as_view(), name="advisor-message-list"),
    path("messages/<int:message_id>/reply/", AdvisorMessageReplyView.as_view(), name="advisor-message-reply"),
    # Staff messaging
    path("staff/messages/", StaffMessageListView.as_view(), name="staff-message-list"),
    path("staff/messages/<int:message_id>/reply/", StaffMessageReplyView.as_view(), name="staff-message-reply"),
    path("staff/send-message/", StaffSendMessageView.as_view(), name="staff-send-message"),
    path("staff/contact-admin/", StaffContactAdminView.as_view(), name="staff-contact-admin"),
    path("staff/my-messages/", StaffMyMessagesView.as_view(), name="staff-my-messages"),
    # Advisor student overview
    path("students/", AdvisorStudentListView.as_view(), name="advisor-student-list"),
    path("students/<int:student_id>/", AdvisorStudentDetailView.as_view(), name="advisor-student-detail"),
]
