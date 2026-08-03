from django.db import models
from django.conf import settings
from apps.courses.models import Course


class CognitiveProfile(models.Model):
    student = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cognitive_profile")
    abstract_reasoning = models.FloatField(default=0)
    logical_reasoning = models.FloatField(default=0)
    theoretical_knowledge = models.FloatField(default=0)
    quantitative_calculation = models.FloatField(default=0)
    practical_application = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def total(self):
        return (
            self.abstract_reasoning
            + self.logical_reasoning
            + self.theoretical_knowledge
            + self.quantitative_calculation
            + self.practical_application
        )

    def __str__(self):
        return f"CognitiveProfile({self.student.email})"


class Recommendation(models.Model):
    REVIEW_CHOICES = [("pending_review", "Pending Review"), ("accepted", "Accepted"), ("rejected", "Rejected")]
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recommendations")
    generated_at = models.DateTimeField(auto_now_add=True)
    selected_courses = models.ManyToManyField(Course)
    explanation = models.TextField()
    rule_snapshot = models.JSONField(default=dict)
    review_status = models.CharField(max_length=16, choices=REVIEW_CHOICES, default="pending_review")
    student_acknowledged = models.BooleanField(default=False)
    student_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="reviewed_recommendations")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Recommendation({self.student.email}, {self.generated_at:%Y-%m-%d})"


class Activity(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activities")
    action = models.CharField(max_length=120)
    detail = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class AdvisorMessage(models.Model):
    RECIPIENT_CHOICES = [("advisor", "Advisor"), ("administrator", "Administrator")]
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="advisor_messages")
    recipient_type = models.CharField(max_length=16, choices=RECIPIENT_CHOICES)
    subject = models.CharField(max_length=160)
    body = models.TextField()
    reply = models.TextField(blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    replied_at = models.DateTimeField(null=True, blank=True)
    reply_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"AdvisorMessage({self.student.email} -> {self.recipient_type})"


class MessageReply(models.Model):
    """Threaded replies within a message thread."""
    message = models.ForeignKey(AdvisorMessage, on_delete=models.CASCADE, related_name="replies")
    sender_type = models.CharField(max_length=16, choices=[("student", "Student"), ("staff", "Staff")])
    sender_name = models.CharField(max_length=120, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Reply({self.sender_type}, {self.message.id})"
