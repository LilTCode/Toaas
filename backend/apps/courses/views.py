from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.exceptions import ValidationError
from .models import Course, TranscriptEntry
from .serializers import CourseSerializer, TranscriptEntrySerializer
from apps.advisories.models import Activity
from apps.advisories.views import recalculate_cognitive_profile, log_activity
from .greedy_classifier import classify_course


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.role == "administrator"


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by("level", "semester", "code")
    serializer_class = CourseSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_permissions(self):
        if self.action == "search":
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    @action(detail=False, methods=["get"])
    def search(self, request):
        query = request.query_params.get("q", "")
        results = self.queryset.filter(code__icontains=query) | self.queryset.filter(title__icontains=query)
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], parser_classes=[JSONParser])
    def auto_classify(self, request):
        title = request.data.get("title", "")
        description = request.data.get("description", "")
        major_topics = request.data.get("major_topics", "")
        learning_objectives = request.data.get("learning_objectives", "")
        profile = classify_course(title, description, major_topics, learning_objectives)
        return Response(profile)

    @action(detail=False, methods=["post"], parser_classes=[MultiPartParser, FormParser])
    def upload_excel(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"detail": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            import openpyxl
            wb = openpyxl.load_workbook(file, read_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
        except Exception as e:
            return Response({"detail": f"Failed to parse Excel file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        if not rows or len(rows) < 2:
            return Response({"detail": "Excel file is empty or has no data rows."}, status=status.HTTP_400_BAD_REQUEST)

        header = [str(c).strip().lower().replace(" ", "_") if c else "" for c in rows[0]]
        required = {"code", "title", "credit_units", "level", "semester"}
        if not required.issubset(set(header)):
            return Response({"detail": f"Excel must have columns: {', '.join(sorted(required))}. Found: {header}"}, status=status.HTTP_400_BAD_REQUEST)

        created = []
        errors = []
        for idx, row in enumerate(rows[1:], start=2):
            if all(c is None or str(c).strip() == "" for c in row):
                continue
            data = {}
            for i, col in enumerate(header):
                val = row[i] if i < len(row) else None
                if col in ("credit_units", "level", "semester"):
                    try:
                        data[col] = int(val) if val is not None else None
                    except (ValueError, TypeError):
                        data[col] = None
                else:
                    data[col] = str(val).strip() if val else ""

            code = data.get("code", "")
            title = data.get("title", "")
            if not code or not title:
                errors.append(f"Row {idx}: missing code or title")
                continue

            if Course.objects.filter(code=code).exists():
                errors.append(f"Row {idx}: course {code} already exists")
                continue

            try:
                cu = int(data.get("credit_units", 3)) if data.get("credit_units") else 3
                lvl = int(data.get("level", 100)) if data.get("level") else 100
                sem = int(data.get("semester", 1)) if data.get("semester") else 1
            except (ValueError, TypeError):
                errors.append(f"Row {idx}: invalid numeric fields")
                continue

            description = data.get("description", "")
            major_topics = data.get("major_topics", "")
            learning_objectives = data.get("learning_objectives", "")
            profile = classify_course(title, description, major_topics, learning_objectives)

            compulsory_raw = str(data.get("is_compulsory", "")).strip().lower()
            is_compulsory = compulsory_raw not in ("false", "no", "0", "elective")

            try:
                course = Course.objects.create(
                    code=code,
                    title=title,
                    credit_units=cu,
                    level=lvl,
                    semester=sem,
                    department_classification=data.get("department_classification", request.data.get("default_programme", "Computer Science")),
                    description=description,
                    major_topics=major_topics,
                    learning_objectives=learning_objectives,
                    is_compulsory=is_compulsory,
                    abstract_reasoning=profile["abstract_reasoning"],
                    logical_reasoning=profile["logical_reasoning"],
                    theoretical_knowledge=profile["theoretical_knowledge"],
                    quantitative_calculation=profile["quantitative_calculation"],
                    practical_application=profile["practical_application"],
                )
            except ValidationError as exc:
                errors.append(f"Row {idx}: {'; '.join(exc.messages)}")
                continue
            created.append({
                "code": course.code,
                "title": course.title,
                "profile": profile,
            })

        return Response({
            "created": len(created),
            "errors": errors,
            "courses": created,
        })


class TranscriptEntryViewSet(viewsets.ModelViewSet):
    serializer_class = TranscriptEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        return TranscriptEntry.objects.filter(student=self.request.user).select_related("course")

    def perform_create(self, serializer):
        entry = serializer.save(student=self.request.user)
        log_activity(self.request.user, "Result added", f"{entry.course.code} — {entry.grade}")
        recalculate_cognitive_profile(self.request.user)

    def perform_update(self, serializer):
        entry = serializer.save()
        log_activity(self.request.user, "Result updated", f"{entry.course.code} — {entry.grade}")
        recalculate_cognitive_profile(self.request.user)

    def perform_destroy(self, instance):
        log_activity(self.request.user, "Result removed", f"{instance.course.code}")
        recalculate_cognitive_profile(self.request.user)
        instance.delete()
