from django.test import TestCase

from apps.accounts.models import User
from apps.courses.models import Course, TranscriptEntry
from apps.advisories.views import build_cognitive_profile_from_transcript, build_course_recommendations


class RecommendationEngineTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="student-001",
            email="student@example.com",
            password="strong-password",
            is_email_verified=True,
            programme="computer_science",
            current_level=400,
            current_semester=1,
        )

        self.analysis_course = Course.objects.create(
            code="CSC301",
            title="Advanced Algorithms",
            credit_units=3,
            semester=1,
            level=300,
            description="Algorithmic reasoning course",
            abstract_reasoning=35,
            logical_reasoning=25,
            theoretical_knowledge=20,
            quantitative_calculation=10,
            practical_application=10,
        )
        self.systems_course = Course.objects.create(
            code="CSC302",
            title="Systems Design",
            credit_units=3,
            semester=2,
            level=300,
            description="Applied systems course",
            abstract_reasoning=15,
            logical_reasoning=20,
            theoretical_knowledge=25,
            quantitative_calculation=20,
            practical_application=20,
        )
        self.elective_course = Course.objects.create(
            code="CSC401",
            title="Research Methods",
            credit_units=3,
            semester=1,
            level=400,
            description="Research driven course",
            abstract_reasoning=25,
            logical_reasoning=20,
            theoretical_knowledge=25,
            quantitative_calculation=15,
            practical_application=15,
        )

        TranscriptEntry.objects.create(
            student=self.student,
            course=self.analysis_course,
            semester="First",
            grade="A",
            credit_points=4.0,
            status="passed",
        )
        TranscriptEntry.objects.create(
            student=self.student,
            course=self.systems_course,
            semester="Second",
            grade="B",
            credit_points=3.0,
            status="passed",
        )

    def test_build_cognitive_profile_from_transcript(self):
        profile = build_cognitive_profile_from_transcript(self.student)

        self.assertGreater(profile["abstract_reasoning"], 0)
        self.assertGreater(profile["logical_reasoning"], 0)
        self.assertGreater(profile["theoretical_knowledge"], 0)

    def test_build_course_recommendations_prefers_matching_courses(self):
        recommendations = build_course_recommendations(self.student)

        self.assertTrue(recommendations)
        self.assertEqual(recommendations[0]["code"], "CSC401")
        self.assertIn("profile", recommendations[0]["explanation"].lower())
