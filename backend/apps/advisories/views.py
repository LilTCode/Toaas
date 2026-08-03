import json
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.utils.timezone import now
from apps.accounts.models import User
from apps.courses.models import Course, TranscriptEntry
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
    transcript_entries = TranscriptEntry.objects.filter(student=student).select_related("course")
    if not transcript_entries.exists():
        return {d: 0 for d in COGNITIVE_DIMENSIONS}

    weighted_score = {d: 0 for d in COGNITIVE_DIMENSIONS}
    total_weight = 0

    for entry in transcript_entries:
        course = entry.course
        if entry.status != "passed":
            continue
        grade_weight = {"A": 1.0, "B": 0.8, "C": 0.6, "D": 0.4, "E": 0.2}.get(entry.grade.upper(), 0.5)
        contribution = max(1, course.credit_units) * grade_weight
        total_weight += contribution
        for dim in COGNITIVE_DIMENSIONS:
            weighted_score[dim] += contribution * (getattr(course, dim) / 100)

    if total_weight == 0:
        return {d: 0 for d in COGNITIVE_DIMENSIONS}

    return {dim: round(weighted_score[dim] / total_weight * 100, 1) for dim in COGNITIVE_DIMENSIONS}


def recalculate_cognitive_profile(student):
    profile_data = build_cognitive_profile_from_transcript(student)
    profile, _ = CognitiveProfile.objects.get_or_create(student=student)
    for dim in COGNITIVE_DIMENSIONS:
        setattr(profile, dim, profile_data[dim])
    profile.save()
    return profile_data


def build_course_recommendations(student):
    """
    Greedy optimisation with Learned Helplessness balancing.
    1. Carryover courses get highest priority.
    2. If multiple carryover courses belong to the student's weakest cognitive dimensions,
       distribute them: only recommend a portion now, defer the rest to future semesters.
    3. Fill remaining units with courses matching the student's strongest dimensions.
    4. Respect 15-24 credit unit policy.
    5. Only recommend courses from the student's own programme and level.
    """
    profile_data = recalculate_cognitive_profile(student)

    # Identify weakest dimensions (bottom 2)
    sorted_dims = sorted(COGNITIVE_DIMENSIONS, key=lambda d: profile_data.get(d, 0))
    weakest_dim = sorted_dims[0]
    second_weakest = sorted_dims[1]

    # Identify strongest dimensions (top 2)
    strongest_dim = sorted_dims[-1]
    second_strongest = sorted_dims[-2]

    # Get programme name for filtering
    programme = student.get_programme_display().replace("B.Sc. ", "")
    current_level = student.current_level
    current_semester = student.current_semester

    # Gather eligible courses — current level (both semesters) + carryovers from previous levels
    # Try current semester first, then fall back to entire level to ensure 15-unit minimum
    level_courses = Course.objects.filter(
        level=current_level,
        department_classification__in=[programme, "Computer Science", "General"],
    )
    carryover_entries = TranscriptEntry.objects.filter(
        student=student, status__in=["failed", "carryover"]
    ).select_related("course")

    course_pool = {}
    for c in level_courses:
        course_pool[c.id] = c
    for entry in carryover_entries:
        course_pool[entry.course_id] = entry.course

    # Remove already-passed courses and prerequisites not met
    eligible = []
    for course in course_pool.values():
        if TranscriptEntry.objects.filter(student=student, course=course, status="passed").exists():
            continue
        prereqs = course.prerequisites.all()
        if prereqs.exists() and any(
            not TranscriptEntry.objects.filter(student=student, course=p, status="passed").exists()
            for p in prereqs
        ):
            continue
        is_co = TranscriptEntry.objects.filter(
            student=student, course=course, status__in=["failed", "carryover"]
        ).exists()
        eligible.append((course, is_co))

    # Score each course by cognitive fit
    scored = []
    for course, is_co in eligible:
        diff = sum(abs(profile_data.get(d, 0) - getattr(course, d, 0)) for d in COGNITIVE_DIMENSIONS) / 5
        # Compute course's dominant cognitive dimension
        course_dims = {d: getattr(course, d, 0) for d in COGNITIVE_DIMENSIONS}
        dominant_dim = max(course_dims, key=course_dims.get)
        scored.append({
            "course": course,
            "carryover": is_co,
            "difference": diff,
            "compatibility": max(0, round(100 - diff)),
            "dominant_dim": dominant_dim,
            "dim_value": course_dims[dominant_dim],
        })

    # Separate carryover and new courses
    carryover_scored = [s for s in scored if s["carryover"]]
    new_scored = [s for s in scored if not s["carryover"]]

    # Learned Helplessness: group carryovers by dominant dimension
    co_by_dim = {}
    for s in carryover_scored:
        co_by_dim.setdefault(s["dominant_dim"], []).append(s)

    # For weakest dimensions, only take a fraction now
    def cap_dim_carryovers(dim, items, max_per_dim=3):
        if dim in (weakest_dim, second_weakest):
            return items[:min(len(items), max_per_dim)]
        return items

    selected_carryovers = []
    for dim, items in co_by_dim.items():
        items.sort(key=lambda x: x["difference"])
        capped = cap_dim_carryovers(dim, items)
        selected_carryovers.extend(capped)
        # Remaining items become deferred
        remaining = [s for s in items if s not in capped]
        # We still store them in rule_snapshot as deferred but don't include in current plan

    # Sort carryovers: best fit first
    selected_carryovers.sort(key=lambda x: x["difference"])

    # Build the final list
    ranked = []
    total_units = 0

    # Add carryover courses first
    for s in selected_carryovers:
        c = s["course"]
        if total_units + c.credit_units > 24:
            continue
        total_units += c.credit_units
        explanation = (
            f"Carryover prioritised — {c.code} was previously incomplete. "
            f"This course strengthens your {s['dominant_dim'].replace('_', ' ')} skills "
            f"which align with your academic development plan."
        )
        ranked.append({
            "id": c.id,
            "code": c.code,
            "title": c.title,
            "credit_units": c.credit_units,
            "level": c.level,
            "semester": c.semester,
            "description": c.description,
            "compatibility": s["compatibility"],
            "carryover": True,
            "explanation": explanation,
            "cognitive_dims": {d: getattr(c, d, 0) for d in COGNITIVE_DIMENSIONS},
        })

    # Add new courses — prefer strongest dimensions
    new_scored.sort(key=lambda x: (x["dominant_dim"] in (weakest_dim, second_weakest), x["difference"]))
    for s in new_scored:
        if total_units + s["course"].credit_units > 24:
            continue
        c = s["course"]
        total_units += c.credit_units
        explanation = (
            f"This course complements your strong {s['dominant_dim'].replace('_', ' ')} abilities "
            f"({profile_data.get(s['dominant_dim'], 0):.1f}% proficiency). "
            f"Compatibility with your cognitive profile is {s['compatibility']}%."
        )
        ranked.append({
            "id": c.id,
            "code": c.code,
            "title": c.title,
            "credit_units": c.credit_units,
            "level": c.level,
            "semester": c.semester,
            "description": c.description,
            "compatibility": s["compatibility"],
            "carryover": False,
            "explanation": explanation,
            "cognitive_dims": {d: getattr(c, d, 0) for d in COGNITIVE_DIMENSIONS},
        })

    # Deferred carryovers (for future semesters)
    deferred = []
    for dim, items in co_by_dim.items():
        items.sort(key=lambda x: x["difference"])
        already_selected_ids = {s["course"].id for s in selected_carryovers}
        for s in items:
            if s["course"].id not in already_selected_ids:
                deferred.append({
                    "id": s["course"].id,
                    "code": s["course"].code,
                    "title": s["course"].title,
                    "credit_units": s["course"].credit_units,
                    "dominant_dim": s["dominant_dim"],
                    "cognitive_dims": {d: getattr(s["course"], d, 0) for d in COGNITIVE_DIMENSIONS},
                })

    return {
        "courses": ranked,
        "total_units": total_units,
        "deferred_courses": deferred,
        "profile": profile_data,
        "sorted_dims": sorted_dims,
        "weakest_dim": weakest_dim,
        "second_weakest": second_weakest,
    }


class CognitiveProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = CognitiveProfile.objects.get_or_create(student=request.user)
        serializer = CognitiveProfileSerializer(profile)
        return Response(serializer.data)


class GenerateRecommendationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        result = build_course_recommendations(request.user)
        profile_data = result["profile"]
        recommendations = result["courses"]
        deferred = result["deferred_courses"]
        sorted_dims = result["sorted_dims"]
        weakest_dim = result["weakest_dim"]
        second_weakest = result["second_weakest"]

        profile, _ = CognitiveProfile.objects.get_or_create(student=request.user)
        for dim in COGNITIVE_DIMENSIONS:
            setattr(profile, dim, profile_data[dim])
        profile.save()

        explanation_parts = [
            f"Your cognitive profile shows strength in {sorted_dims[-1].replace('_', ' ')} ({profile_data.get(sorted_dims[-1], 0):.1f}%) "
            f"and {sorted_dims[-2].replace('_', ' ')} ({profile_data.get(sorted_dims[-2], 0):.1f}%)."
        ]
        if deferred:
            explanation_parts.append(
                f"To avoid overwhelming your weaker areas ({weakest_dim.replace('_', ' ')}, {second_weakest.replace('_', ' ')}), "
                f"{len(deferred)} carryover course(s) have been deferred to future semesters."
            )

        recommendation = Recommendation.objects.create(
            student=request.user,
            explanation=" ".join(explanation_parts),
            rule_snapshot={
                "profile": profile_data,
                "courses": recommendations,
                "deferred_courses": deferred,
                "total_units": result["total_units"],
                "course_count": len(recommendations),
            },
            review_status="pending_review",
        )
        course_ids = [item["id"] for item in recommendations]
        if course_ids:
            recommendation.selected_courses.set(Course.objects.filter(id__in=course_ids))
        recommendation.save(update_fields=["rule_snapshot"])

        log_activity(
            request.user, "Recommendation generated",
            f"{len(recommendations)} courses, {result['total_units']} units"
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
        recommendation = Recommendation.objects.get(id=recommendation_id, student=request.user)
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
            grade_points = sum(
                {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1, "F": 0}.get(e.grade.upper(), 0)
                for e in transcript if e.grade
            )
            cgpa = round(grade_points / total, 2) if total > 0 else 0.0

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
        grade_points = sum(
            {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1, "F": 0}.get(e.grade.upper(), 0)
            for e in transcript if e.grade
        )
        cgpa = round(grade_points / total, 2) if total > 0 else 0.0

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
