import json
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.timezone import now
from apps.accounts.models import User
from apps.courses.models import Course, TranscriptEntry
from .engine import build_plan, compute_cgpa, compute_mastery, profile_from_mastery
from .models import CognitiveProfile, Recommendation, Activity, AdvisorMessage, MessageReply
from .serializers import (
    CognitiveProfileSerializer, RecommendationSerializer, ActivitySerializer,
    AdvisorMessageSerializer, MessageReplySerializer,
)
from apps.accounts.serializers import UserSerializer


COGNITIVE_DIMENSIONS = [
    "abstract_reasoning",
    "logical_reasoning",
    "theoretical_knowledge",
    "quantitative_calculation",
    "practical_application",
]


def log_activity(student, action, detail=""):
    Activity.objects.create(student=student, action=action, detail=detail)


def build_cognitive_profile_from_transcript(student):
    """Relative-strength profile (percentages summing to 100) from the transcript.

    Delegates to the advisory engine so the persisted profile, the transcript
    recalculation, and the recommendation plan all describe the same student.
    """
    mastery, _evidence, _confidence = compute_mastery(student)
    return profile_from_mastery(mastery)


def recalculate_cognitive_profile(student):
    profile_data = build_cognitive_profile_from_transcript(student)
    profile, _ = CognitiveProfile.objects.get_or_create(student=student)
    for dim in COGNITIVE_DIMENSIONS:
        setattr(profile, dim, profile_data[dim])
    profile.save()
    return profile_data


class CognitiveProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = CognitiveProfile.objects.get_or_create(student=request.user)
        serializer = CognitiveProfileSerializer(profile)
        return Response(serializer.data)


class GenerateRecommendationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        student = request.user
        plan = build_plan(student)

        profile_data = plan["profile"]
        recommendations = plan["courses"]
        deferred = plan["deferred_courses"]
        total_units = plan["total_units"]

        # Persist the engine's profile (sums to 100%) so the profile endpoint,
        # charts, and the plan all describe the same student.
        profile, _ = CognitiveProfile.objects.get_or_create(student=student)
        for dim in COGNITIVE_DIMENSIONS:
            setattr(profile, dim, profile_data.get(dim, 0))
        profile.save()

        recommendation = Recommendation.objects.create(
            student=student,
            explanation=plan["explanation"],
            rule_snapshot={
                "profile": profile_data,
                "mastery": plan["mastery"],
                "courses": recommendations,
                "deferred_courses": deferred,
                "total_units": total_units,
                "course_count": len(recommendations),
                "min_units": plan["min_units"],
                "max_units": plan["max_units"],
                "meets_policy": plan["meets_policy"],
                "warnings": plan["warnings"],
                "helplessness": plan["helplessness"],
                "failure_counts": plan["failure_counts"],
                "evidence": plan["evidence"],
                "cognitive_load": plan["cognitive_load"],
                "strain_budgets": plan["strain_budgets"],
                "next_cycle": plan["next_cycle"],
            },
            review_status="pending_review",
        )
        course_ids = [item["id"] for item in recommendations]
        if course_ids:
            recommendation.selected_courses.set(Course.objects.filter(id__in=course_ids))

        log_activity(
            request.user, "Recommendation generated",
            f"{len(recommendations)} courses, {total_units} units"
        )
        serializer = RecommendationSerializer(recommendation)
        return Response(serializer.data)


class RecommendationListView(generics.ListAPIView):
    serializer_class = RecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Recommendation.objects.filter(student=self.request.user).order_by("-generated_at")


class RecommendationAcknowledgeView(APIView):
    """Student acknowledges the recommendation plan (OK button)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, recommendation_id):
        try:
            recommendation = Recommendation.objects.get(
                id=recommendation_id, student=request.user
            )
        except Recommendation.DoesNotExist:
            return Response(
                {"detail": "Recommendation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        recommendation.student_acknowledged = True
        recommendation.student_note = request.data.get("student_note", "")
        recommendation.save(update_fields=["student_acknowledged", "student_note"])
        log_activity(request.user, "Recommendation acknowledged", "Student reviewed the plan")
        return Response(RecommendationSerializer(recommendation).data)


class AdvisorRecommendationReviewView(APIView):
    """Advisor accepts or rejects a student's recommendation plan."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, student_id):
        if request.user.role not in ("advisor", "administrator"):
            return Response({"detail": "Not authorised"}, status=status.HTTP_403_FORBIDDEN)

        decision = request.data.get("decision")
        if decision not in ("accepted", "rejected"):
            return Response({"detail": "Decision must be accepted or rejected."}, status=status.HTTP_400_BAD_REQUEST)

        recommendation = Recommendation.objects.filter(student_id=student_id).order_by("-generated_at").first()
        if not recommendation:
            return Response({"detail": "No recommendation plan found for this student."}, status=status.HTTP_404_NOT_FOUND)

        recommendation.review_status = decision
        recommendation.reviewed_by = request.user
        recommendation.reviewed_at = now()
        recommendation.review_notes = request.data.get("review_notes", "")
        recommendation.save(update_fields=["review_status", "reviewed_by", "reviewed_at", "review_notes"])

        log_activity(recommendation.student, f"Recommendation {decision} by advisor", request.data.get("review_notes", ""))
        return Response(RecommendationSerializer(recommendation).data)


class ActivityListView(generics.ListAPIView):
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Activity.objects.filter(student=self.request.user)[:20]


# ──────────────────────────────────────────────
# Advisor / Admin Staff Message Views
# ──────────────────────────────────────────────

class StaffSendMessageView(APIView):
    """Staff (advisor/admin) send a new message to a student."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.role not in ("advisor", "administrator"):
            return Response({"detail": "Not authorised"}, status=status.HTTP_403_FORBIDDEN)

        student_id = request.data.get("student_id")
        subject = request.data.get("subject", "Advisor message")
        body = request.data.get("body", "").strip()

        if not student_id or not body:
            return Response({"detail": "student_id and body are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = User.objects.get(id=student_id, role="student")
        except User.DoesNotExist:
            return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        msg = AdvisorMessage.objects.create(
            student=student,
            recipient_type="advisor" if request.user.role == "advisor" else "administrator",
            subject=subject,
            body=body,
        )
        return Response({
            "id": msg.id,
            "detail": "Message sent to student."
        }, status=status.HTTP_201_CREATED)


class StaffMyMessagesView(APIView):
    """Advisor sees their own messages to admin with replies."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != "advisor":
            return Response({"detail": "Not authorised"}, status=status.HTTP_403_FORBIDDEN)
        messages = AdvisorMessage.objects.filter(
            student=request.user, recipient_type="administrator"
        ).order_by("-created_at")
        data = []
        for m in messages:
            data.append({
                "id": m.id,
                "subject": m.subject,
                "body": m.body,
                "replies": MessageReplySerializer(m.replies.all(), many=True).data,
                "reply_count": m.reply_count,
                "created_at": m.created_at,
            })
        return Response(data)


class StaffContactAdminView(APIView):
    """Advisor contacts the admin/support team."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.role != "advisor":
            return Response({"detail": "Only advisors can contact admin."}, status=status.HTTP_403_FORBIDDEN)

        subject = request.data.get("subject", "").strip()
        body = request.data.get("body", "").strip()
        if not subject or not body:
            return Response({"detail": "Subject and body are required."}, status=status.HTTP_400_BAD_REQUEST)

        msg = AdvisorMessage.objects.create(
            student=request.user,
            recipient_type="administrator",
            subject=subject,
            body=body,
        )
        return Response({"id": msg.id, "detail": "Message sent to admin."}, status=status.HTTP_201_CREATED)


class StaffMessageListView(APIView):
    """Advisors & admins see only their own messages — strictly isolated."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == "advisor":
            messages = AdvisorMessage.objects.filter(
                recipient_type="advisor"
            ).select_related("student").order_by("-created_at")
        elif user.role == "administrator":
            messages = AdvisorMessage.objects.filter(
                recipient_type="administrator"
            ).select_related("student").order_by("-created_at")
        else:
            return Response([], status=status.HTTP_403_FORBIDDEN)

        data = []
        for m in messages:
            replies = MessageReplySerializer(m.replies.all(), many=True).data
            data.append({
                "id": m.id,
                "student_name": m.student.get_full_name() or m.student.email,
                "student_email": m.student.email,
                "recipient_type": m.recipient_type,
                "subject": m.subject,
                "body": m.body,
                "reply": m.reply,
                "replies": replies,
                "read": m.read,
                "reply_count": m.reply_count,
                "created_at": m.created_at,
                "replied_at": m.replied_at,
            })
        return Response(data)


class StaffMessageReplyView(APIView):
    """Staff (advisor/admin) reply to a student message."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, message_id):
        try:
            message = AdvisorMessage.objects.get(id=message_id)
        except AdvisorMessage.DoesNotExist:
            return Response({"detail": "Message not found."}, status=status.HTTP_404_NOT_FOUND)

        # Verify staff role matches message recipient_type — strictly isolated
        user = request.user
        if user.role == "advisor" and message.recipient_type != "advisor":
            return Response({"detail": "This message is not yours."}, status=status.HTTP_403_FORBIDDEN)
        if user.role == "administrator" and message.recipient_type != "administrator":
            return Response({"detail": "This message is not yours."}, status=status.HTTP_403_FORBIDDEN)
        if user.role not in ("advisor", "administrator"):
            return Response({"detail": "Only advisors and admins can reply."}, status=status.HTTP_403_FORBIDDEN)

        content = request.data.get("content", "").strip()
        if not content:
            return Response({"detail": "Content is required."}, status=status.HTTP_400_BAD_REQUEST)

        staff_name = f"{user.get_full_name() or user.email} ({'Advisor' if user.role == 'advisor' else 'Admin'})"

        reply = MessageReply.objects.create(
            message=message,
            sender_type="staff",
            sender_name=staff_name,
            content=content,
        )

        message.reply = content  # Keep the last reply field synced
        message.reply_count = message.replies.count()
        message.read = True
        message.replied_at = reply.created_at
        message.save(update_fields=["reply", "reply_count", "read", "replied_at"])

        return Response(MessageReplySerializer(reply).data, status=status.HTTP_201_CREATED)


# ──────────────────────────────────────────────
# Student Views
# ──────────────────────────────────────────────

class AdvisorMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = AdvisorMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AdvisorMessage.objects.filter(student=self.request.user)

    def perform_create(self, serializer):
        message = serializer.save(student=self.request.user)
        log_activity(self.request.user, "Message sent", f"Sent to {message.get_recipient_type_display()}")


class AdvisorMessageReplyView(APIView):
    """Student replies to a message thread."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, message_id):
        try:
            message = AdvisorMessage.objects.get(id=message_id, student=request.user)
        except AdvisorMessage.DoesNotExist:
            return Response({"detail": "Message not found."}, status=status.HTTP_404_NOT_FOUND)

        content = request.data.get("content", "").strip()
        if not content:
            return Response({"detail": "Content is required."}, status=status.HTTP_400_BAD_REQUEST)

        reply = MessageReply.objects.create(
            message=message,
            sender_type="student",
            sender_name=request.user.get_full_name() or request.user.email,
            content=content,
        )

        message.reply_count = message.replies.count()
        message.read = True
        message.save(update_fields=["reply_count", "read"])

        log_activity(request.user, "Replied to message", f"Added reply to: {message.subject}")
        return Response(MessageReplySerializer(reply).data, status=status.HTTP_201_CREATED)


# ──────────────────────────────────────────────
# Advisor Student Overview Views
# ──────────────────────────────────────────────

class AdvisorStudentListView(APIView):
    """Advisor sees all registered students with cognitive profiles."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in ("advisor", "administrator"):
            return Response({"detail": "Not authorised"}, status=status.HTTP_403_FORBIDDEN)

        students = User.objects.filter(role="student").order_by("current_level", "last_name")
        data = []
        for s in students:
            profile, _ = CognitiveProfile.objects.get_or_create(student=s)
            transcript = TranscriptEntry.objects.filter(student=s)
            total = transcript.count()
            cgpa = compute_cgpa(s)

            data.append({
                "id": s.id,
                "first_name": s.first_name,
                "last_name": s.last_name,
                "full_name": s.get_full_name(),
                "email": s.email,
                "username": s.username,
                "programme": s.programme,
                "programme_display": s.get_programme_display(),
                "current_level": s.current_level,
                "current_semester": s.current_semester,
                "session": s.session,
                "profile_photo": s.profile_photo.url if s.profile_photo else None,
                "cgpa": cgpa,
                "cognitive_profile": CognitiveProfileSerializer(profile).data,
                "transcript_count": total,
            })
        return Response(data)


class AdvisorStudentDetailView(APIView):
    """Detailed view of a single student for advisor."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, student_id):
        if request.user.role not in ("advisor", "administrator"):
            return Response({"detail": "Not authorised"}, status=status.HTTP_403_FORBIDDEN)

        try:
            student = User.objects.get(id=student_id, role="student")
        except User.DoesNotExist:
            return Response({"detail": "Student not found"}, status=status.HTTP_404_NOT_FOUND)

        profile, _ = CognitiveProfile.objects.get_or_create(student=student)
        transcript = TranscriptEntry.objects.filter(student=student).select_related("course")
        total = transcript.count()
        cgpa = compute_cgpa(student)

        # Carryover courses
        carryovers = transcript.filter(status__in=["failed", "carryover"])
        carryover_data = []
        for e in carryovers:
            carryover_data.append({
                "id": e.id,
                "course_code": e.course.code,
                "course_title": e.course.title,
                "credit_units": e.course.credit_units,
                "semester": e.semester,
                "grade": e.grade,
                "status": e.status,
            })

        # Latest recommendation
        latest_rec = Recommendation.objects.filter(student=student).order_by("-generated_at").first()
        rec_data = None
        if latest_rec:
            rec_data = RecommendationSerializer(latest_rec).data

        # Transcript summary
        transcript_summary = []
        for e in transcript:
            transcript_summary.append({
                "id": e.id,
                "course_code": e.course.code,
                "course_title": e.course.title,
                "credit_units": e.course.credit_units,
                "semester": e.semester,
                "grade": e.grade,
                "status": e.status,
            })

        # AI conversation history
        from apps.chatbot.models import ChatConversation
        conversations = ChatConversation.objects.filter(student=student).order_by("-updated_at")[:5]
        chat_history = []
        for conv in conversations:
            msgs = conv.messages.all().values("sender_role", "content", "created_at")
            chat_history.append({
                "conversation_id": conv.id,
                "created_at": conv.created_at,
                "messages": list(msgs),
            })

        # Advisor messages between this student and this advisor
        advisor_msgs = AdvisorMessage.objects.filter(
            student=student, recipient_type="advisor"
        ).order_by("-created_at")
        msg_data = []
        for m in advisor_msgs:
            msg_data.append({
                "id": m.id,
                "subject": m.subject,
                "body": m.body,
                "reply_count": m.reply_count,
                "created_at": m.created_at,
                "replies": MessageReplySerializer(m.replies.all(), many=True).data,
            })

        return Response({
            "student": {
                "id": student.id,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "full_name": student.get_full_name(),
                "email": student.email,
                "username": student.username,
                "programme": student.programme,
                "programme_display": student.get_programme_display(),
                "current_level": student.current_level,
                "current_semester": student.current_semester,
                "session": student.session,
                "profile_photo": student.profile_photo.url if student.profile_photo else None,
                "cgpa": cgpa,
            },
            "cognitive_profile": CognitiveProfileSerializer(profile).data,
            "transcript": transcript_summary,
            "carryovers": carryover_data,
            "recommendation": rec_data,
            "chat_history": chat_history,
            "advisor_messages": msg_data,
        })
