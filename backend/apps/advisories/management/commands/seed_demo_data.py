from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import User
from apps.courses.models import Course, TranscriptEntry
from apps.advisories.models import CognitiveProfile, Activity, AdvisorMessage, MessageReply
from apps.advisories.views import recalculate_cognitive_profile, build_course_recommendations
from apps.chatbot.models import ChatConversation, ChatMessage
from apps.advisories.models import Recommendation


class Command(BaseCommand):
    help = "Seed complete demo data — users, transcript, cognitive profiles, messages, chats"

    def handle(self, *args, **options):
        # ── Create demo accounts ──────────────────────────────
        admin, _ = User.objects.get_or_create(
            email="admin@toaas.edu",
            defaults={
                "username": "admin",
                "first_name": "System",
                "last_name": "Admin",
                "role": "administrator",
                "is_email_verified": True,
                "is_staff": True,
                "is_active": True,
            },
        )
        admin.set_password("admin1234")
        admin.save()

        advisor, _ = User.objects.get_or_create(
            email="advisor@toaas.edu",
            defaults={
                "username": "advisor1",
                "first_name": "Dr. Ade",
                "last_name": "Bello",
                "role": "advisor",
                "is_email_verified": True,
                "is_active": True,
            },
        )
        advisor.set_password("advisor1234")
        advisor.save()

        # ── Create student: Alex (Software Engineering, 200L, strong in practical, weak in calculation) ──
        alex, _ = User.objects.get_or_create(
            email="alex@demo.edu",
            defaults={
                "username": "SEN2022001",
                "first_name": "Alex",
                "last_name": "Okafor",
                "role": "student",
                "programme": "software_engineering",
                "current_level": 200,
                "current_semester": 1,
                "session": "2025/2026",
                "is_email_verified": True,
                "is_active": True,
                "profile_photo": "",
            },
        )
        alex.set_password("demo1234")
        alex.advisor = advisor
        alex.save()

        # ── Create student: Sarah (Cyber Security, 300L, strong in theoretical, weak in abstract) ──
        sarah, _ = User.objects.get_or_create(
            email="sarah@demo.edu",
            defaults={
                "username": "CYB2021001",
                "first_name": "Sarah",
                "last_name": "Mohammed",
                "role": "student",
                "programme": "cyber_security",
                "current_level": 300,
                "current_semester": 1,
                "session": "2025/2026",
                "is_email_verified": True,
                "is_active": True,
            },
        )
        sarah.set_password("demo1234")
        sarah.advisor = advisor
        sarah.save()

        # ── Create student: James (Computer Science, 200L, carryover-heavy in quantitative) ──
        james, _ = User.objects.get_or_create(
            email="james@demo.edu",
            defaults={
                "username": "CSC2022001",
                "first_name": "James",
                "last_name": "Eze",
                "role": "student",
                "programme": "computer_science",
                "current_level": 200,
                "current_semester": 1,
                "session": "2025/2026",
                "is_email_verified": True,
                "is_active": True,
            },
        )
        james.set_password("demo1234")
        james.advisor = advisor
        james.save()

        self.stdout.write("Demo accounts created: admin@toaas.edu / admin1234, advisor@toaas.edu / advisor1234, alex@demo.edu / demo1234, sarah@demo.edu / demo1234, james@demo.edu / demo1234")

        # ── Clean up old transcript & profile data before re-seeding ──
        for student in [alex, sarah, james]:
            TranscriptEntry.objects.filter(student=student).delete()
            CognitiveProfile.objects.filter(student=student).delete()
            Recommendation.objects.filter(student=student).delete()
            Activity.objects.filter(student=student).delete()
        self.stdout.write("Cleared existing transcript, profiles, recommendations, and activities.")

        # ── Seed transcript entries for Alex ─────────────────
        # Alex: strong in practical, weak in calculation (MTH/PHY got D/E — passed but weak)
        alex_entries = [
            ("GST101", "A", "passed", "First"), ("GST102", "A", "passed", "First"),
            ("MTH101", "C", "passed", "First"), ("PHY101", "C", "passed", "First"),
            ("CSC101", "A", "passed", "First"), ("SEN101", "A", "passed", "First"),
            ("CYB101", "B", "passed", "First"),
            ("GST111", "A", "passed", "Second"), ("MTH102", "D", "passed", "Second"),
            ("PHY102", "D", "passed", "Second"), ("CSC102", "A", "passed", "Second"),
            ("SEN102", "A", "passed", "Second"), ("CYB102", "B", "passed", "Second"),
        ]
        self._seed_transcript(alex, alex_entries)

        # ── Seed transcript for Sarah ────────────────────
        sarah_entries = [
            ("GST101", "A", "passed", "First"), ("GST102", "B", "passed", "First"),
            ("MTH101", "B", "passed", "First"), ("PHY101", "B", "passed", "First"),
            ("CSC101", "A", "passed", "First"), ("CYB101", "A", "passed", "First"),
            ("GST111", "A", "passed", "Second"), ("MTH102", "C", "passed", "Second"),
            ("PHY102", "C", "passed", "Second"), ("CSC102", "B", "passed", "Second"),
            ("CYB102", "A", "passed", "Second"),
            ("CSC201", "A", "passed", "First"), ("CSC202", "B", "passed", "First"),
            ("CSC203", "B", "passed", "First"), ("CYB201", "A", "passed", "First"),
            ("MTH201", "C", "passed", "First"),
            ("CSC211", "A", "passed", "Second"), ("CSC212", "B", "passed", "Second"),
            ("CSC213", "A", "passed", "Second"), ("CYB211", "B", "passed", "Second"),
            ("GST212", "A", "passed", "Second"),
        ]
        self._seed_transcript(sarah, sarah_entries)

        # ── Seed transcript for James (carryovers are truly failed F-grade courses) ──
        # D and E are passed but weak; only F-grades become carryover
        james_entries = [
            ("GST101", "B", "passed", "First"), ("GST102", "C", "passed", "First"),
            ("MTH101", "D", "passed", "First"), ("PHY101", "D", "passed", "First"),
            ("CSC101", "C", "passed", "First"),
            ("GST111", "B", "passed", "Second"), ("MTH102", "E", "passed", "Second"),
            ("PHY102", "E", "passed", "Second"), ("CSC102", "C", "passed", "Second"),
            ("CSC201", "C", "passed", "First"), ("CSC202", "D", "passed", "First"),
            ("CSC203", "C", "passed", "First"), ("MTH201", "F", "carryover", "First"),
        ]
        self._seed_transcript(james, james_entries)

        self.stdout.write("Transcript entries seeded for all demo students.")

        # ── Recalculate cognitive profiles ────────────────
        for student in [alex, sarah, james]:
            recalculate_cognitive_profile(student)
            cp = CognitiveProfile.objects.get(student=student)
            self.stdout.write(f"  {student.email} profile: AR={cp.abstract_reasoning:.1f} LR={cp.logical_reasoning:.1f} TK={cp.theoretical_knowledge:.1f} QC={cp.quantitative_calculation:.1f} PA={cp.practical_application:.1f}")

        # ── Generate recommendations for each student ──────
        for student in [alex, sarah, james]:
            result = build_course_recommendations(student)
            rec = Recommendation.objects.create(
                student=student,
                explanation=f"Demo recommendation for {student.first_name}",
                rule_snapshot={
                    "profile": result["profile"],
                    "courses": result["courses"],
                    "deferred_courses": result["deferred_courses"],
                    "total_units": result["total_units"],
                    "course_count": len(result["courses"]),
                },
            )
            course_ids = [c["id"] for c in result["courses"]]
            if course_ids:
                rec.selected_courses.set(Course.objects.filter(id__in=course_ids))
            rec.save()
            self.stdout.write(f"  {student.first_name}: {len(result['courses'])} recommended, {len(result['deferred_courses'])} deferred")

        # ── Seed activities ────────────────────────────────
        for student in [alex, sarah, james]:
            Activity.objects.create(student=student, action="Transcript uploaded", detail="Academic records processed")
            Activity.objects.create(student=student, action="Cognitive profile computed", detail="All results analysed")
            Activity.objects.create(student=student, action="Recommendation generated", detail="Course plan ready for review")
        self.stdout.write("Activities seeded.")

        # ── AI Chat conversations ──────────────────────────
        for student in [alex, sarah]:
            conv = ChatConversation.objects.create(student=student)
            ChatMessage.objects.create(conversation=conv, sender_role="student", content="Why was CSC 201 recommended for me?")
            ChatMessage.objects.create(conversation=conv, sender_role="system",
                content="CSC 201 (Data Structures) was recommended because your cognitive profile shows strong practical application (%.1f%%). Data Structures builds on that strength while improving your logical reasoning."
            )
        self.stdout.write("Chat conversations seeded.")

        # ── Advisor messages ───────────────────────────────
        msg1 = AdvisorMessage.objects.create(
            student=alex, recipient_type="advisor",
            subject="Course load concern",
            body="I'm worried about taking too many calculation-heavy courses this semester. Can I defer some?"
        )
        MessageReply.objects.create(message=msg1, sender_type="staff",
            sender_name="Dr. Ade Bello (Advisor)",
            content="Good afternoon Alex. Based on your cognitive profile, the system has already balanced your load. You'll only take 2 calculation-based courses this semester — the rest are aligned with your strengths. We can discuss further if you have concerns."
        )

        AdvisorMessage.objects.create(
            student=james, recipient_type="advisor",
            subject="Help with carryover courses",
            body="I have MTH102 and PHY102 as carryovers plus MTH201. That's too many calculations at once."
        )

        AdvisorMessage.objects.create(
            student=sarah, recipient_type="administrator",
            subject="System access issue",
            body="I can't view my transcript on mobile. The table doesn't scroll horizontally."
        )
        self.stdout.write("Advisor messages seeded.")

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully!"))

    def _seed_transcript(self, student, entries):
        for code, grade, status, semester in entries:
            try:
                course = Course.objects.get(code=code)
                grade_points = {"A": 5.0, "B": 4.0, "C": 3.0, "D": 2.0, "E": 1.0, "F": 0.0}
                TranscriptEntry.objects.get_or_create(
                    student=student,
                    course=course,
                    semester=semester,
                    defaults={
                        "grade": grade,
                        "credit_points": grade_points.get(grade, 0),
                        "status": status,
                    },
                )
            except Course.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Course {code} not found — skipping"))
