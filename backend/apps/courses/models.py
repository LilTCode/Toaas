from django.db import models
from django.conf import settings
import re


class Course(models.Model):
    SEMESTER_CHOICES = [(1, "First"), (2, "Second")]
    LEVEL_CHOICES = [(100, "100"), (200, "200"), (300, "300"), (400, "400")]

    code = models.CharField(max_length=16, unique=True)
    title = models.CharField(max_length=255)
    credit_units = models.PositiveSmallIntegerField()
    semester = models.PositiveSmallIntegerField(choices=SEMESTER_CHOICES)
    level = models.PositiveSmallIntegerField(choices=LEVEL_CHOICES)
    prerequisites = models.ManyToManyField("self", blank=True, symmetrical=False)
    description = models.TextField(blank=True)
    learning_objectives = models.TextField(blank=True)
    major_topics = models.TextField(blank=True)
    recommended_references = models.TextField(blank=True)
    department_classification = models.CharField(max_length=128, default="Computer Science")
    metadata = models.JSONField(blank=True, null=True)

    # Compulsory courses cannot be quietly dropped from a plan — when the engine
    # has to defer one it raises a warning for advisor sign-off instead.
    is_compulsory = models.BooleanField(default=True)
    # Retired courses stay in the table for historical transcripts but are never
    # recommended again.
    is_active = models.BooleanField(default=True)

    abstract_reasoning = models.PositiveSmallIntegerField(default=0)
    logical_reasoning = models.PositiveSmallIntegerField(default=0)
    theoretical_knowledge = models.PositiveSmallIntegerField(default=0)
    quantitative_calculation = models.PositiveSmallIntegerField(default=0)
    practical_application = models.PositiveSmallIntegerField(default=0)

    def cognitive_total(self):
        return (
            self.abstract_reasoning
            + self.logical_reasoning
            + self.theoretical_knowledge
            + self.quantitative_calculation
            + self.practical_application
        )

    @staticmethod
    def semester_from_code(code):
        """Semester implied by the course code, per university numbering policy.

        The last digit of the course number carries the semester: odd numbers are
        first-semester courses, even numbers are second-semester ones — CSC201 is
        taught in first semester, CSC202 in second. Returns ``None`` when the code
        has no digits to read.
        """
        match = re.search(r"(\d+)", code or "")
        if not match:
            return None
        return 1 if int(match.group(1)[-1]) % 2 == 1 else 2

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.cognitive_total() != 100:
            raise ValidationError("Cognitive demand percentages must total 100%.")

        implied = self.semester_from_code(self.code)
        if implied is not None and self.semester != implied:
            raise ValidationError(
                f"{self.code} ends in "
                f"{'an odd' if implied == 1 else 'an even'} digit, so it is a "
                f"{'first' if implied == 1 else 'second'}-semester course, but "
                f"semester {self.semester} was given. Renumber the course or fix "
                f"the semester."
            )

    def save(self, *args, **kwargs):
        # Derive the semester from the code so every write path agrees — bulk
        # importers call create()/save() directly and bypass ModelForm validation.
        implied = self.semester_from_code(self.code)
        if implied is not None:
            self.semester = implied
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.title}"


class TranscriptEntry(models.Model):
    STATUS_CHOICES = [
        ("passed", "Passed"),
        ("failed", "Failed"),
        ("in_progress", "In Progress"),
        ("carryover", "Carryover"),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transcript_entries")
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.CharField(max_length=32)
    grade = models.CharField(max_length=8, blank=True)
    credit_points = models.FloatField(default=0)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "course", "semester")

    def __str__(self):
        return f"{self.student.email} - {self.course.code} ({self.status})"
