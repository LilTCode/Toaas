from django.test import TestCase

from apps.accounts.models import User
from apps.courses.models import Course, TranscriptEntry
from apps.courses.greedy_classifier import classify_course
from apps.advisories import engine
from apps.advisories.engine import (
    build_plan, build_candidates, compute_mastery, compute_helplessness,
)


def make_course(code, title, level, semester, **dims):
    """Create a 3-unit course with the given cognitive demand split (sums to 100)."""
    defaults = dict(
        abstract_reasoning=0, logical_reasoning=0, theoretical_knowledge=0,
        quantitative_calculation=0, practical_application=0,
    )
    defaults.update(dims)
    assert sum(defaults.values()) == 100, f"{code} cognitive dims must total 100: {defaults}"
    return Course.objects.create(
        code=code, title=title, credit_units=3, level=level, semester=semester,
        department_classification="Computer Science", **defaults,
    )


class RecommendationEngineTests(TestCase):
    """Validates the constrained-greedy engine against the advisory policy."""

    def setUp(self):
        self.student = User.objects.create_user(
            username="student-001",
            email="student@example.com",
            password="strong-password",
            is_email_verified=True,
            programme="computer_science",
            current_level=300,
            current_semester=1,
            session="2025/2026",
        )

        # Passed courses: strong in logical/theoretical/practical, weak in calculation.
        passed = [
            make_course("CSC201", "Data Structures", 200, 1,
                        logical_reasoning=40, practical_application=40, theoretical_knowledge=20),
            make_course("GST201", "Philosophy & Logic", 200, 1,
                        theoretical_knowledge=70, logical_reasoning=30),
            make_course("CSC204", "Web Development", 200, 2,
                        practical_application=80, abstract_reasoning=20),
        ]
        grades = {"CSC201": ("B", 4.0), "GST201": ("A", 5.0), "CSC204": ("B", 4.0)}
        for course in passed:
            grade, points = grades[course.code]
            TranscriptEntry.objects.create(
                student=self.student, course=course, semester="First",
                grade=grade, credit_points=points, status="passed",
            )

        # Four quantitative-heavy carryovers at 200-level, semester 1 (odd codes).
        self.carryovers = [
            make_course("MTH201", "Discrete Math II", 200, 1,
                        quantitative_calculation=80, practical_application=20),
            make_course("MTH203", "Linear Algebra II", 200, 1,
                        quantitative_calculation=80, practical_application=20),
            make_course("MTH205", "Numerical Analysis I", 200, 1,
                        quantitative_calculation=80, practical_application=20),
            make_course("PHY201", "Physics II", 200, 1,
                        quantitative_calculation=70, practical_application=30),
        ]
        for course in self.carryovers:
            TranscriptEntry.objects.create(
                student=self.student, course=course, semester="First",
                grade="F", credit_points=0.0, status="failed",
            )

        # A second-semester carryover that must never appear in this first-semester plan.
        self.sem2_carryover = make_course("MTH204", "Calculus II", 200, 2,
                                          quantitative_calculation=80, practical_application=20)
        TranscriptEntry.objects.create(
            student=self.student, course=self.sem2_carryover, semester="Second",
            grade="F", credit_points=0.0, status="failed",
        )

        # Current-level (300) semester-1 courses, mostly non-quantitative, so the
        # 15-unit floor can be reached without relaxing the calculation strain cap.
        self.new_courses = [
            make_course("CSC301", "Advanced Data Structures", 300, 1,
                        logical_reasoning=40, practical_application=40, theoretical_knowledge=20),
            make_course("CSC305", "Database Systems", 300, 1,
                        practical_application=60, theoretical_knowledge=20, logical_reasoning=20),
            make_course("CSC303", "Operating Systems", 300, 1,
                        theoretical_knowledge=40, practical_application=30, logical_reasoning=30),
            make_course("GST301", "Nigerian Peoples & Culture", 300, 1,
                        theoretical_knowledge=60, abstract_reasoning=40),
            # Semester-2 course — must be excluded from a first-semester plan.
            make_course("CSC312", "Artificial Intelligence", 300, 2,
                        abstract_reasoning=40, quantitative_calculation=30, logical_reasoning=30),
        ]

    def test_only_semester_matching_courses_are_offered(self):
        plan = build_plan(self.student)
        offered = plan["courses"] + plan["deferred_courses"]
        self.assertTrue(offered)
        self.assertTrue(all(c["semester"] == 1 for c in offered))
        codes = {c["code"] for c in offered}
        self.assertNotIn("CSC312", codes)  # 2nd-semester new course
        self.assertNotIn("MTH204", codes)  # 2nd-semester carryover

    def test_carryovers_are_prioritised_first(self):
        plan = build_plan(self.student)
        self.assertTrue(plan["courses"])
        self.assertTrue(plan["courses"][0]["carryover"])

    def test_cognitive_balance_defers_some_calc_carryovers(self):
        plan = build_plan(self.student)
        selected_calc_co = [c for c in plan["courses"] if c["carryover"]]
        self.assertGreater(len(selected_calc_co), 0)
        self.assertLess(len(selected_calc_co), len(self.carryovers))
        deferred_calc = [
            c for c in plan["deferred_courses"]
            if c["code"] in {co.code for co in self.carryovers}
        ]
        self.assertTrue(deferred_calc, "some calc carryovers should be deferred")

    def test_unit_policy_is_respected(self):
        plan = build_plan(self.student)
        self.assertGreaterEqual(plan["total_units"], plan["min_units"])
        self.assertLessEqual(plan["total_units"], plan["max_units"])
        self.assertTrue(plan["meets_policy"], plan["warnings"])

    def test_compatibility_reflects_student_strength(self):
        mastery, _, _ = compute_mastery(self.student)
        helplessness, _ = compute_helplessness(self.student)
        candidates, _ = build_candidates(self.student, mastery, helplessness)
        compat = {c["code"]: c["compatibility"] for c in candidates}
        # The calculation-heavy carryover must score below the practical course.
        self.assertGreater(compat["CSC305"], compat["MTH201"])


def _student(username, email, **kwargs):
    kwargs.setdefault("programme", "computer_science")
    kwargs.setdefault("current_level", 300)
    kwargs.setdefault("current_semester", 1)
    kwargs.setdefault("session", "2025/2026")
    return User.objects.create_user(
        username=username, email=email, password="strong-password",
        is_email_verified=True, **kwargs
    )


def _course(code, level=200, semester=1, units=3, **dims):
    defaults = dict(
        abstract_reasoning=0, logical_reasoning=0, theoretical_knowledge=0,
        quantitative_calculation=0, practical_application=0,
    )
    defaults.update(dims)
    assert sum(defaults.values()) == 100, f"{code}: {defaults}"
    return Course.objects.create(
        code=code, title=f"Course {code}", credit_units=units, level=level,
        semester=semester, department_classification="Computer Science", **defaults,
    )


def _record(student, course, grade, status="passed", semester="2024/2025 First"):
    points = {"A": 5.0, "B": 4.0, "C": 3.0, "D": 2.0, "E": 1.0, "F": 0.0}
    return TranscriptEntry.objects.create(
        student=student, course=course, semester=semester, grade=grade,
        credit_points=points.get(grade, 0.0), status=status,
    )


class MasteryModelTests(TestCase):
    """The profile must measure performance, not curriculum exposure."""

    def test_identical_course_different_grade_gives_different_mastery(self):
        top = _student("A/1", "a@example.com")
        weak = _student("B/1", "b@example.com")
        course = _course("MTH201", quantitative_calculation=80, practical_application=20)

        _record(top, course, "A")
        _record(weak, course, "D")

        mastery_top, _, _ = compute_mastery(top)
        mastery_weak, _, _ = compute_mastery(weak)

        self.assertGreater(
            mastery_top["quantitative_calculation"],
            mastery_weak["quantitative_calculation"],
            "An A and a D in the same course used to produce identical profiles.",
        )

    def test_scraping_passes_is_not_reported_as_strength(self):
        """The inversion the previous implementation produced.

        Six calculation courses passed with D grades plus two theory courses
        passed with A grades used to rank calculation as the student's top
        dimension, because the grade cancelled out of the weighted average.
        """
        student = _student("C/1", "c@example.com")
        for i in range(6):
            _record(student, _course(f"MTH21{i}", quantitative_calculation=80,
                                     practical_application=20), "D")
        for i in range(2):
            _record(student, _course(f"GST21{i}", theoretical_knowledge=80,
                                     abstract_reasoning=20), "A")

        mastery, _, _ = compute_mastery(student)
        self.assertLess(
            mastery["quantitative_calculation"],
            mastery["theoretical_knowledge"],
            "Scraping D grades in calculation must not outrank A grades in theory.",
        )

    def test_failures_are_evidence_not_absence_of_evidence(self):
        student = _student("D/1", "d@example.com")
        _record(student, _course("MTH202", quantitative_calculation=80,
                                 practical_application=20), "F", status="failed")

        mastery, evidence, _ = compute_mastery(student)
        self.assertGreater(evidence["quantitative_calculation"], 0)
        self.assertLess(mastery["quantitative_calculation"], 50.0)

    def test_cold_start_is_neutral_and_flagged_low_confidence(self):
        student = _student("E/1", "e@example.com", current_level=100)
        mastery, evidence, confidence = compute_mastery(student)
        for dim in engine.COGNITIVE_DIMENSIONS:
            self.assertEqual(mastery[dim], 50.0)
            self.assertEqual(evidence[dim], 0.0)
            self.assertEqual(confidence[dim], 0.0)

    def test_helplessness_escalates_with_repeat_failures(self):
        once = _student("F/1", "f@example.com")
        thrice = _student("G/1", "g@example.com")
        first = _course("MTH220", quantitative_calculation=80, practical_application=20)
        second = _course("MTH221", quantitative_calculation=80, practical_application=20)

        _record(once, first, "F", status="failed", semester="2023/2024 First")
        for term in ("2022/2023 First", "2023/2024 First", "2024/2025 First"):
            _record(thrice, second, "F", status="failed", semester=term)

        h_once, _ = compute_helplessness(once)
        h_thrice, _ = compute_helplessness(thrice)
        self.assertGreater(
            h_thrice["quantitative_calculation"],
            h_once["quantitative_calculation"],
        )

    def test_cgpa_is_credit_unit_weighted(self):
        student = _student("H/1", "h@example.com")
        _record(student, _course("BIG101", units=6, theoretical_knowledge=100), "A")
        _record(student, _course("SML101", units=1, theoretical_knowledge=100), "F",
                status="failed")
        # (5*6 + 0*1) / 7 = 4.29 — not the unweighted mean of 2.5
        self.assertEqual(engine.compute_cgpa(student), 4.29)


class LevelAndPrerequisiteTests(TestCase):
    def test_hundred_level_student_sees_only_hundred_level(self):
        student = _student("I/1", "i@example.com", current_level=100)
        for i in (1, 3, 5, 7, 9):
            _course(f"CSC10{i}", level=100, semester=1, theoretical_knowledge=100)
        _course("CSC111", level=100, semester=1, theoretical_knowledge=100)
        _course("CSC201", level=200, semester=1, theoretical_knowledge=100)

        plan = build_plan(student)
        self.assertTrue(plan["courses"])
        self.assertTrue(all(c["level"] == 100 for c in plan["courses"]))

    def test_courses_above_current_level_are_never_offered(self):
        student = _student("J/1", "j@example.com", current_level=300)
        _course("CSC301", level=300, semester=1, theoretical_knowledge=100)
        _course("CSC401", level=400, semester=1, theoretical_knowledge=100)

        plan = build_plan(student)
        offered = {c["code"] for c in plan["courses"] + plan["deferred_courses"]}
        self.assertNotIn("CSC401", offered)

    def test_passed_courses_are_never_recommended_again(self):
        student = _student("K/1", "k@example.com")
        passed = _course("CSC301", level=300, semester=1, theoretical_knowledge=100)
        _record(student, passed, "B")
        _course("CSC303", level=300, semester=1, theoretical_knowledge=100)

        plan = build_plan(student)
        self.assertNotIn("CSC301", {c["code"] for c in plan["courses"]})

    def test_unmet_prerequisites_block_and_are_explained(self):
        student = _student("L/1", "l@example.com")
        prereq = _course("CSC201", level=200, semester=1, theoretical_knowledge=100)
        advanced = _course("CSC301", level=300, semester=1, theoretical_knowledge=100)
        advanced.prerequisites.add(prereq)
        _course("CSC303", level=300, semester=1, theoretical_knowledge=100)

        plan = build_plan(student)
        self.assertNotIn("CSC301", {c["code"] for c in plan["courses"]})
        blocked = [d for d in plan["deferred_courses"] if d["code"] == "CSC301"]
        self.assertTrue(blocked)
        self.assertIn("CSC201", blocked[0]["missing_prerequisites"])
        self.assertTrue(blocked[0]["explanation"])


class UnitPolicyTests(TestCase):
    def test_shortfall_is_reported_rather_than_hidden(self):
        student = _student("M/1", "m@example.com")
        _course("CSC301", level=300, semester=1, theoretical_knowledge=100)

        plan = build_plan(student)
        self.assertLess(plan["total_units"], plan["min_units"])
        self.assertFalse(plan["meets_policy"])
        self.assertTrue(plan["warnings"], "A sub-minimum plan must warn the student.")

    def test_ceiling_is_never_exceeded(self):
        student = _student("N/1", "n@example.com")
        for i in range(1, 24, 2):
            _course(f"CSC3{i:02d}", level=300, semester=1, units=3,
                    theoretical_knowledge=50, practical_application=50)

        plan = build_plan(student)
        self.assertLessEqual(plan["total_units"], plan["max_units"])
        self.assertEqual(
            plan["total_units"], sum(c["credit_units"] for c in plan["courses"])
        )


class DeferralAndProjectionTests(TestCase):
    def setUp(self):
        self.student = _student("O/1", "o@example.com", current_level=300)
        # A realistic history: solid in practical work, failing calculation.
        for i in (1, 3):
            _record(self.student, _course(f"CSC21{i}", level=200, semester=1,
                                          practical_application=70,
                                          theoretical_knowledge=30), "A")
        for i in (1, 3, 5):
            course = _course(f"MTH20{i}", level=200, semester=1,
                             quantitative_calculation=80, practical_application=20)
            _record(self.student, course, "F", status="failed")
        for i in (1, 3):
            _course(f"MTH30{i}", level=300, semester=1,
                    quantitative_calculation=80, practical_application=20)
        for i in (1, 3, 5, 7):
            _course(f"CSC30{i}", level=300, semester=1,
                    practical_application=60, theoretical_knowledge=40)
        self.plan = build_plan(self.student)

    def test_combined_calculation_load_stays_within_budget(self):
        """The old cap only counted carryovers, so new courses slipped past it."""
        load = self.plan["cognitive_load"]["quantitative_calculation"]
        budget = self.plan["strain_budgets"]["quantitative_calculation"]
        self.assertLessEqual(round(load, 2), round(budget, 2))

    def test_deferred_courses_carry_a_reason_and_a_destination(self):
        deferred = self.plan["deferred_courses"]
        self.assertTrue(deferred)
        for item in deferred:
            self.assertTrue(item["explanation"])
        scheduled = [d for d in deferred if "deferred_to_session" in d]
        self.assertTrue(scheduled)
        for item in scheduled:
            self.assertEqual(item["deferred_to_session"], "2026/2027")
            self.assertEqual(item["deferred_to_semester"], 1)

    def test_next_cycle_replans_deferred_work_in_the_same_semester(self):
        projection = self.plan["next_cycle"]
        self.assertEqual(projection["session"], "2026/2027")
        self.assertEqual(projection["semester"], self.student.current_semester)
        self.assertEqual(projection["level"], 400)
        self.assertLessEqual(projection["total_units"], engine.MAX_UNITS)

    def test_plan_retains_courses_the_student_can_win(self):
        anchors = [
            c for c in self.plan["courses"]
            if c["expected_success"] >= engine.ANCHOR_THRESHOLD
        ]
        self.assertTrue(
            anchors,
            "A plan made entirely of high-risk courses reinforces helplessness.",
        )

    def test_no_safe_course_is_escalated_rather_than_hidden(self):
        """A student with nothing but failures has no winnable course to offer.

        The engine cannot manufacture one, so it must say so instead of
        presenting a high-risk plan as if it were balanced.
        """
        struggling = _student("Q/1", "q@example.com", current_level=300)
        for i in (1, 3, 5):
            _record(struggling, _course(f"MTH25{i}", level=200, semester=1,
                                        quantitative_calculation=80,
                                        practical_application=20),
                    "F", status="failed")
        for i in (1, 3, 5):
            _course(f"MTH35{i}", level=300, semester=1,
                    quantitative_calculation=80, practical_application=20)

        plan = build_plan(struggling)
        self.assertTrue(plan["courses"])
        self.assertFalse(
            [c for c in plan["courses"]
             if c["expected_success"] >= engine.ANCHOR_THRESHOLD]
        )
        self.assertTrue(
            any("confidence mark" in w for w in plan["warnings"]),
            f"Expected an escalation warning, got {plan['warnings']}",
        )


class CompatibilityScoreTests(TestCase):
    def test_score_spreads_across_the_range(self):
        """The old mean-absolute-difference score was locked into 60-100%."""
        student = _student("P/1", "p@example.com")
        for i in range(3):
            _record(student, _course(f"MTH23{i}", quantitative_calculation=80,
                                     practical_application=20), "F", status="failed")
        for i in range(3):
            _record(student, _course(f"CSC23{i}", practical_application=80,
                                     theoretical_knowledge=20), "A")

        mastery, _, _ = compute_mastery(student)
        helplessness, _ = compute_helplessness(student)

        hard = _course("MTH301", level=300, quantitative_calculation=80,
                       practical_application=20)
        easy = _course("CSC301", level=300, practical_application=80,
                       theoretical_knowledge=20)

        hard_score, _ = engine.expected_success(hard, mastery, helplessness)
        easy_score, _ = engine.expected_success(easy, mastery, helplessness)

        self.assertGreater(easy_score - hard_score, 20)
        self.assertLess(hard_score, 60)


class ClassifierTests(TestCase):
    def test_percentages_always_total_100(self):
        samples = [
            ("Elementary Mathematics I", ""),
            ("Communication in English", "essay writing and grammar"),
            ("", ""),
            ("Data Structures and Algorithms", "abstract data types, complexity"),
            ("Software Laboratory", "hands-on practical build exercises"),
        ]
        for title, description in samples:
            profile = classify_course(title, description)
            self.assertEqual(sum(profile.values()), 100, f"{title!r} -> {profile}")
            self.assertTrue(all(v >= 0 for v in profile.values()))

    def test_hyphenated_keywords_match(self):
        """'hands-on' and 'real-world' were written as regex but matched literally."""
        profile = classify_course("Software Workshop", "hands-on, real-world practice")
        self.assertEqual(max(profile, key=profile.get), "practical_application")

    def test_substring_false_positive_removed(self):
        """'database' must not register as quantitative via the 'data' keyword."""
        profile = classify_course("Database Systems", "relational database design")
        self.assertLess(
            profile["quantitative_calculation"], profile["practical_application"]
        )

    def test_model_rejects_cognitive_totals_that_are_not_100(self):
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            Course.objects.create(
                code="BAD101", title="Invalid", credit_units=3, semester=1, level=100,
                abstract_reasoning=50, logical_reasoning=50, theoretical_knowledge=50,
                quantitative_calculation=50, practical_application=50,
            )


class SessionArithmeticTests(TestCase):
    def test_next_session_increments_both_years(self):
        self.assertEqual(engine.next_session("2025/2026"), "2026/2027")

    def test_next_session_tolerates_unexpected_input(self):
        self.assertEqual(engine.next_session(""), "")
        self.assertEqual(engine.next_session("odd-format"), "odd-format")


class CourseNumberingPolicyTests(TestCase):
    """Odd course numbers are first-semester, even numbers are second."""

    def test_semester_is_read_from_the_last_digit(self):
        self.assertEqual(Course.semester_from_code("CSC101"), 1)
        self.assertEqual(Course.semester_from_code("CSC102"), 2)
        self.assertEqual(Course.semester_from_code("MTH203"), 1)
        self.assertEqual(Course.semester_from_code("GST204"), 2)
        self.assertEqual(Course.semester_from_code("CSC411"), 1)
        self.assertIsNone(Course.semester_from_code("NODIGITS"))

    def test_semester_is_derived_on_save_regardless_of_input(self):
        course = Course.objects.create(
            code="CSC207", title="Odd numbered", credit_units=3,
            semester=2,  # contradicts the code — must be corrected, not accepted
            level=200, theoretical_knowledge=100,
        )
        self.assertEqual(course.semester, 1)

        course.code = "CSC208"
        course.save()
        self.assertEqual(course.semester, 2)

    def test_seeded_catalogue_obeys_the_policy(self):
        from apps.courses.management.commands.seed_courses import ALL_COURSES

        for item in ALL_COURSES:
            self.assertEqual(
                Course.semester_from_code(item["code"]), item["semester"],
                f"{item['code']} is declared semester {item['semester']} but its "
                f"number says otherwise",
            )

    def test_seeded_catalogue_has_no_duplicate_codes(self):
        from apps.courses.management.commands.seed_courses import ALL_COURSES

        codes = [item["code"] for item in ALL_COURSES]
        self.assertEqual(len(codes), len(set(codes)))

    def test_every_programme_can_reach_the_unit_floor_each_semester(self):
        """A legal 15-unit registration must be possible everywhere."""
        from apps.courses.management.commands.seed_courses import ALL_COURSES

        pools = {
            "Computer Science": {"Computer Science", "General"},
            "Software Engineering": {"Software Engineering", "Computer Science", "General"},
            "Cyber Security": {"Cyber Security", "Computer Science", "General"},
        }
        for programme, depts in pools.items():
            for level in (100, 200, 300, 400):
                for semester in (1, 2):
                    units = sum(
                        c["credit_units"] for c in ALL_COURSES
                        if c["level"] == level
                        and c["semester"] == semester
                        and c["department_classification"] in depts
                    )
                    self.assertGreaterEqual(
                        units, engine.MIN_UNITS,
                        f"{programme} L{level} S{semester} offers only {units} units",
                    )

    def test_second_semester_course_cannot_enter_a_first_semester_plan(self):
        student = _student("R/1", "r@example.com", current_level=200,
                           current_semester=1)
        odd = _course("CSC201", level=200, semester=1, theoretical_knowledge=100)
        even = _course("CSC202", level=200, semester=2, theoretical_knowledge=100)
        # Both codes drive their own semester, so the pairing is guaranteed.
        self.assertEqual(odd.semester, 1)
        self.assertEqual(even.semester, 2)

        plan = build_plan(student)
        offered = {c["code"] for c in plan["courses"] + plan["deferred_courses"]}
        self.assertIn("CSC201", offered)
        self.assertNotIn("CSC202", offered)
