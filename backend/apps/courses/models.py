from django.db import models
from django.conf import settings


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

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.cognitive_total() != 100:
            raise ValidationError("Cognitive demand percentages must total 100%.")

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
