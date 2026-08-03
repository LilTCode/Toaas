from django.core.management.base import BaseCommand
from apps.courses.models import Course


PROGRAMMES = {
    "cs": "Computer Science",
    "se": "Software Engineering",
    "cyb": "Cyber Security",
}

ALL_COURSES = [
    # ── 100 Level – First Semester ──────────────────────────────
    {
        "code": "GST101", "title": "Communication in English I", "credit_units": 2,
        "semester": 1, "level": 100,
        "department_classification": "General",
        "abstract_reasoning": 5, "logical_reasoning": 15,
        "theoretical_knowledge": 40, "quantitative_calculation": 5,
        "practical_application": 35,
    },
    {
        "code": "GST102", "title": "Philosophy & Logic", "credit_units": 2,
        "semester": 1, "level": 100,
        "department_classification": "General",
        "abstract_reasoning": 30, "logical_reasoning": 30,
        "theoretical_knowledge": 25, "quantitative_calculation": 5,
        "practical_application": 10,
    },
    {
        "code": "MTH101", "title": "Elementary Mathematics I", "credit_units": 3,
        "semester": 1, "level": 100,
        "department_classification": "Computer Science",
        "abstract_reasoning": 15, "logical_reasoning": 20,
        "theoretical_knowledge": 15, "quantitative_calculation": 40,
        "practical_application": 10,
    },
    {
        "code": "PHY101", "title": "General Physics I", "credit_units": 3,
        "semester": 1, "level": 100,
        "department_classification": "Computer Science",
        "abstract_reasoning": 10, "logical_reasoning": 15,
        "theoretical_knowledge": 25, "quantitative_calculation": 35,
        "practical_application": 15,
    },
    {
        "code": "CSC101", "title": "Introduction to Computer Science", "credit_units": 3,
        "semester": 1, "level": 100,
        "department_classification": "Computer Science",
        "abstract_reasoning": 15, "logical_reasoning": 20,
        "theoretical_knowledge": 25, "quantitative_calculation": 15,
        "practical_application": 25,
    },
    {
        "code": "SEN101", "title": "Fundamentals of Software Eng.", "credit_units": 3,
        "semester": 1, "level": 100,
        "department_classification": "Software Engineering",
        "abstract_reasoning": 20, "logical_reasoning": 20,
        "theoretical_knowledge": 20, "quantitative_calculation": 10,
        "practical_application": 30,
    },
    {
        "code": "CYB101", "title": "Introduction to Cyber Security", "credit_units": 3,
        "semester": 1, "level": 100,
        "department_classification": "Cyber Security",
        "abstract_reasoning": 25, "logical_reasoning": 20,
        "theoretical_knowledge": 25, "quantitative_calculation": 10,
        "practical_application": 20,
    },

    # ── 100 Level – Second Semester ─────────────────────────────
    {
        "code": "GST111", "title": "Communication in English II", "credit_units": 2,
        "semester": 2, "level": 100,
        "department_classification": "General",
        "abstract_reasoning": 5, "logical_reasoning": 15,
        "theoretical_knowledge": 35, "quantitative_calculation": 5,
        "practical_application": 40,
    },
    {
        "code": "MTH102", "title": "Elementary Mathematics II", "credit_units": 3,
        "semester": 2, "level": 100,
        "department_classification": "Computer Science",
        "abstract_reasoning": 10, "logical_reasoning": 20,
        "theoretical_knowledge": 15, "quantitative_calculation": 45,
        "practical_application": 10,
    },
    {
        "code": "PHY102", "title": "General Physics II", "credit_units": 3,
        "semester": 2, "level": 100,
        "department_classification": "Computer Science",
        "abstract_reasoning": 10, "logical_reasoning": 15,
        "theoretical_knowledge": 20, "quantitative_calculation": 40,
        "practical_application": 15,
    },
    {
        "code": "CSC102", "title": "Computer Programming I", "credit_units": 3,
        "semester": 2, "level": 100,
        "department_classification": "Computer Science",
        "abstract_reasoning": 15, "logical_reasoning": 25,
        "theoretical_knowledge": 15, "quantitative_calculation": 10,
        "practical_application": 35,
    },
    {
        "code": "SEN102", "title": "Introduction to Web Development", "credit_units": 3,
        "semester": 2, "level": 100,
        "department_classification": "Software Engineering",
        "abstract_reasoning": 10, "logical_reasoning": 15,
        "theoretical_knowledge": 15, "quantitative_calculation": 10,
        "practical_application": 50,
    },
    {
        "code": "CYB102", "title": "Digital Ethics & Law", "credit_units": 3,
        "semester": 2, "level": 100,
        "department_classification": "Cyber Security",
        "abstract_reasoning": 25, "logical_reasoning": 20,
        "theoretical_knowledge": 30, "quantitative_calculation": 5,
        "practical_application": 20,
    },

    {
        "code": "GST201", "title": "Nigerian Peoples & Culture", "credit_units": 2,
        "semester": 2, "level": 200,
        "department_classification": "General",
        "abstract_reasoning": 5, "logical_reasoning": 10,
        "theoretical_knowledge": 45, "quantitative_calculation": 5,
        "practical_application": 35,
    },

    # ── 200 Level – First Semester ──────────────────────────────
    {
        "code": "CSC201", "title": "Data Structures", "credit_units": 3,
        "semester": 1, "level": 200,
        "department_classification": "Computer Science",
        "abstract_reasoning": 25, "logical_reasoning": 25,
        "theoretical_knowledge": 15, "quantitative_calculation": 15,
        "practical_application": 20,
    },
    {
        "code": "CSC202", "title": "Discrete Mathematics", "credit_units": 3,
        "semester": 1, "level": 200,
        "department_classification": "Computer Science",
        "abstract_reasoning": 30, "logical_reasoning": 25,
        "theoretical_knowledge": 20, "quantitative_calculation": 15,
        "practical_application": 10,
    },
    {
        "code": "CSC203", "title": "Object-Oriented Programming", "credit_units": 3,
        "semester": 1, "level": 200,
        "department_classification": "Computer Science",
        "abstract_reasoning": 15, "logical_reasoning": 20,
        "theoretical_knowledge": 15, "quantitative_calculation": 10,
        "practical_application": 40,
    },
    {
        "code": "MTH201", "title": "Linear Algebra", "credit_units": 3,
        "semester": 1, "level": 200,
        "department_classification": "Computer Science",
        "abstract_reasoning": 10, "logical_reasoning": 15,
        "theoretical_knowledge": 20, "quantitative_calculation": 45,
        "practical_application": 10,
    },
    {
        "code": "SEN201", "title": "Software Requirements Eng.", "credit_units": 3,
        "semester": 1, "level": 200,
        "department_classification": "Software Engineering",
        "abstract_reasoning": 20, "logical_reasoning": 25,
        "theoretical_knowledge": 25, "quantitative_calculation": 10,
        "practical_application": 20,
    },
    {
        "code": "CYB201", "title": "Network Security Fundamentals", "credit_units": 3,
        "semester": 1, "level": 200,
        "department_classification": "Cyber Security",
        "abstract_reasoning": 20, "logical_reasoning": 15,
        "theoretical_knowledge": 25, "quantitative_calculation": 15,
        "practical_application": 25,
    },

    # ── 200 Level – Second Semester ─────────────────────────────
    {
        "code": "CSC211", "title": "Operating Systems", "credit_units": 3,
        "semester": 2, "level": 200,
        "department_classification": "Computer Science",
        "abstract_reasoning": 15, "logical_reasoning": 20,
        "theoretical_knowledge": 25, "quantitative_calculation": 15,
        "practical_application": 25,
    },
    {
        "code": "CSC212", "title": "Computer Architecture", "credit_units": 3,
        "semester": 2, "level": 200,
        "department_classification": "Computer Science",
        "abstract_reasoning": 15, "logical_reasoning": 15,
        "theoretical_knowledge": 25, "quantitative_calculation": 20,
        "practical_application": 25,
    },
    {
        "code": "CSC213", "title": "Database Systems", "credit_units": 3,
        "semester": 2, "level": 200,
        "department_classification": "Computer Science",
        "abstract_reasoning": 10, "logical_reasoning": 20,
        "theoretical_knowledge": 25, "quantitative_calculation": 10,
        "practical_application": 35,
    },
    {
        "code": "SEN211", "title": "UI/UX Design", "credit_units": 3,
        "semester": 2, "level": 200,
        "department_classification": "Software Engineering",
        "abstract_reasoning": 15, "logical_reasoning": 10,
        "theoretical_knowledge": 15, "quantitative_calculation": 5,
        "practical_application": 55,
    },
    {
        "code": "CYB211", "title": "Cryptography I", "credit_units": 3,
        "semester": 2, "level": 200,
        "department_classification": "Cyber Security",
        "abstract_reasoning": 30, "logical_reasoning": 25,
        "theoretical_knowledge": 20, "quantitative_calculation": 15,
        "practical_application": 10,
    },
    {
        "code": "GST212", "title": "Entrepreneurship", "credit_units": 2,
        "semester": 2, "level": 200,
        "department_classification": "General",
        "abstract_reasoning": 10, "logical_reasoning": 15,
        "theoretical_knowledge": 25, "quantitative_calculation": 15,
        "practical_application": 35,
    },

    # ── 300 Level – First Semester ──────────────────────────────
    {
        "code": "CSC301", "title": "Advanced Algorithms", "credit_units": 3,
        "semester": 1, "level": 300,
        "department_classification": "Computer Science",
        "abstract_reasoning": 35, "logical_reasoning": 30,
        "theoretical_knowledge": 15, "quantitative_calculation": 10,
        "practical_application": 10,
    },
    {
        "code": "CSC302", "title": "Systems Design", "credit_units": 3,
        "semester": 1, "level": 300,
        "department_classification": "Computer Science",
        "abstract_reasoning": 15, "logical_reasoning": 20,
        "theoretical_knowledge": 20, "quantitative_calculation": 20,
        "practical_application": 25,
    },
    {
        "code": "CSC303", "title": "Computer Networks", "credit_units": 3,
        "semester": 1, "level": 300,
        "department_classification": "Computer Science",
        "abstract_reasoning": 15, "logical_reasoning": 20,
        "theoretical_knowledge": 25, "quantitative_calculation": 15,
        "practical_application": 25,
    },
    {
        "code": "CSC304", "title": "Software Project Management", "credit_units": 3,
        "semester": 1, "level": 300,
        "department_classification": "Software Engineering",
        "abstract_reasoning": 20, "logical_reasoning": 20,
        "theoretical_knowledge": 20, "quantitative_calculation": 10,
        "practical_application": 30,
    },
    {
        "code": "CYB301", "title": "Ethical Hacking", "credit_units": 3,
        "semester": 1, "level": 300,
        "department_classification": "Cyber Security",
        "abstract_reasoning": 25, "logical_reasoning": 20,
        "theoretical_knowledge": 15, "quantitative_calculation": 10,
        "practical_application": 30,
    },
    {
        "code": "SEN301", "title": "Software Testing & QA", "credit_units": 3,
        "semester": 1, "level": 300,
        "department_classification": "Software Engineering",
        "abstract_reasoning": 15, "logical_reasoning": 25,
        "theoretical_knowledge": 20, "quantitative_calculation": 10,
        "practical_application": 30,
    },

    {
        "code": "GST301", "title": "Entrepreneurship II", "credit_units": 2,
        "semester": 1, "level": 300,
        "department_classification": "General",
        "abstract_reasoning": 10, "logical_reasoning": 15,
        "theoretical_knowledge": 25, "quantitative_calculation": 10,
        "practical_application": 40,
    },

    # ── 300 Level – Second Semester ─────────────────────────────
    {
        "code": "CSC311", "title": "Artificial Intelligence", "credit_units": 3,
        "semester": 2, "level": 300,
        "department_classification": "Computer Science",
        "abstract_reasoning": 30, "logical_reasoning": 25,
        "theoretical_knowledge": 15, "quantitative_calculation": 15,
        "practical_application": 15,
    },
    {
        "code": "CSC312", "title": "Compiler Construction", "credit_units": 3,
        "semester": 2, "level": 300,
        "department_classification": "Computer Science",
        "abstract_reasoning": 35, "logical_reasoning": 25,
        "theoretical_knowledge": 20, "quantitative_calculation": 10,
        "practical_application": 10,
    },
    {
        "code": "CSC313", "title": "Human-Computer Interaction", "credit_units": 3,
        "semester": 2, "level": 300,
        "department_classification": "Computer Science",
        "abstract_reasoning": 15, "logical_reasoning": 15,
        "theoretical_knowledge": 20, "quantitative_calculation": 5,
        "practical_application": 45,
    },
    {
        "code": "SEN311", "title": "DevOps & Continuous Delivery", "credit_units": 3,
        "semester": 2, "level": 300,
        "department_classification": "Software Engineering",
        "abstract_reasoning": 10, "logical_reasoning": 15,
        "theoretical_knowledge": 15, "quantitative_calculation": 10,
        "practical_application": 50,
    },
    {
        "code": "CYB311", "title": "Digital Forensics", "credit_units": 3,
        "semester": 2, "level": 300,
        "department_classification": "Cyber Security",
        "abstract_reasoning": 20, "logical_reasoning": 25,
        "theoretical_knowledge": 20, "quantitative_calculation": 10,
        "practical_application": 25,
    },

    # ── 400 Level – First Semester ──────────────────────────────
    {
        "code": "CSC401", "title": "Research Methods", "credit_units": 3,
        "semester": 1, "level": 400,
        "department_classification": "Computer Science",
        "abstract_reasoning": 25, "logical_reasoning": 20,
        "theoretical_knowledge": 30, "quantitative_calculation": 10,
        "practical_application": 15,
    },
    {
        "code": "CSC402", "title": "Software Engineering", "credit_units": 3,
        "semester": 1, "level": 400,
        "department_classification": "Computer Science",
        "abstract_reasoning": 20, "logical_reasoning": 20,
        "theoretical_knowledge": 20, "quantitative_calculation": 10,
        "practical_application": 30,
    },
    {
        "code": "CSC403", "title": "Distributed Systems", "credit_units": 3,
        "semester": 1, "level": 400,
        "department_classification": "Computer Science",
        "abstract_reasoning": 25, "logical_reasoning": 20,
        "theoretical_knowledge": 20, "quantitative_calculation": 15,
        "practical_application": 20,
    },
    {
        "code": "SEN401", "title": "Cloud Computing", "credit_units": 3,
        "semester": 1, "level": 400,
        "department_classification": "Software Engineering",
        "abstract_reasoning": 15, "logical_reasoning": 20,
        "theoretical_knowledge": 20, "quantitative_calculation": 15,
        "practical_application": 30,
    },
    {
        "code": "CYB401", "title": "Security Operations Center", "credit_units": 3,
        "semester": 1, "level": 400,
        "department_classification": "Cyber Security",
        "abstract_reasoning": 20, "logical_reasoning": 20,
        "theoretical_knowledge": 25, "quantitative_calculation": 10,
        "practical_application": 25,
    },

    # ── 400 Level – Second Semester ─────────────────────────────
    {
        "code": "CSC411", "title": "Project & Thesis", "credit_units": 6,
        "semester": 2, "level": 400,
        "department_classification": "Computer Science",
        "abstract_reasoning": 15, "logical_reasoning": 15,
        "theoretical_knowledge": 20, "quantitative_calculation": 10,
        "practical_application": 40,
    },
    {
        "code": "CSC412", "title": "Professional Practice", "credit_units": 2,
        "semester": 2, "level": 400,
        "department_classification": "Computer Science",
        "abstract_reasoning": 10, "logical_reasoning": 15,
        "theoretical_knowledge": 30, "quantitative_calculation": 5,
        "practical_application": 40,
    },
    {
        "code": "SEN411", "title": "Software Maintenance & Evolution", "credit_units": 3,
        "semester": 2, "level": 400,
        "department_classification": "Software Engineering",
        "abstract_reasoning": 20, "logical_reasoning": 20,
        "theoretical_knowledge": 20, "quantitative_calculation": 10,
        "practical_application": 30,
    },
    {
        "code": "CYB411", "title": "Cyber Security Capstone", "credit_units": 3,
        "semester": 2, "level": 400,
        "department_classification": "Cyber Security",
        "abstract_reasoning": 25, "logical_reasoning": 20,
        "theoretical_knowledge": 20, "quantitative_calculation": 10,
        "practical_application": 25,
    },
]

COURSE_REQUISITES = {
    "CSC202": ["MTH102"],
    "CSC212": ["CSC102"],
    "CSC301": ["CSC201"],
    "CSC311": ["CSC201"],
    "CSC312": ["CSC201"],
    "CSC403": ["CSC303"],
    "SEN301": ["SEN201"],
    "SEN311": ["SEN201"],
    "CYB301": ["CYB201"],
    "CYB311": ["CYB201"],
    "CYB401": ["CYB301"],
}


class Command(BaseCommand):
    help = "Seed comprehensive courses for all programmes and levels"

    def handle(self, *args, **options):
        created_count = 0
        for item in ALL_COURSES:
            _, created = Course.objects.get_or_create(
                code=item["code"],
                defaults=item,
            )
            if created:
                created_count += 1

        # Set prerequisites
        for code, prereq_codes in COURSE_REQUISITES.items():
            try:
                course = Course.objects.get(code=code)
                for prereq_code in prereq_codes:
                    try:
                        prereq = Course.objects.get(code=prereq_code)
                        course.prerequisites.add(prereq)
                    except Course.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"Prerequisite {prereq_code} not found for {code}"))
            except Course.DoesNotExist:
                pass

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {created_count} new courses ({Course.objects.count()} total) "
            f"across all programmes and levels."
        ))
