from rest_framework import serializers
from .models import CognitiveProfile, Recommendation, Activity, AdvisorMessage, MessageReply
from apps.courses.serializers import CourseSerializer


class CognitiveProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CognitiveProfile
        fields = [
            "id",
            "abstract_reasoning",
            "logical_reasoning",
            "theoretical_knowledge",
            "quantitative_calculation",
            "practical_application",
            "updated_at",
        ]


class RecommendationSerializer(serializers.ModelSerializer):
    selected_courses = CourseSerializer(many=True, read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Recommendation
        fields = [
            "id", "generated_at", "selected_courses", "explanation", "rule_snapshot",
            "review_status", "student_acknowledged", "student_note",
            "reviewed_by", "reviewed_by_name", "reviewed_at", "review_notes",
        ]
        read_only_fields = ["reviewed_by_name", "reviewed_at"]

    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return obj.reviewed_by.get_full_name() or obj.reviewed_by.email
        return None


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ["id", "action", "detail", "created_at"]


class MessageReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageReply
        fields = ["id", "sender_type", "sender_name", "content", "created_at"]


class AdvisorMessageSerializer(serializers.ModelSerializer):
    replies = MessageReplySerializer(many=True, read_only=True)

    class Meta:
        model = AdvisorMessage
        fields = ["id", "recipient_type", "subject", "body", "reply", "replies", "read", "reply_count", "created_at", "replied_at"]
        read_only_fields = ["reply", "replies", "read", "reply_count", "created_at", "replied_at"]
