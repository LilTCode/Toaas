from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class MatricNumberValidator(RegexValidator):
    regex = r'^[\w.@+\-/]+$'
    message = 'Enter a valid matric number. It may contain letters, numbers, and /.-@+_ characters.'


class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[MatricNumberValidator()],
    )
    PROGRAMME_CHOICES = [
        ("computer_science", "B.Sc. Computer Science"),
        ("software_engineering", "B.Sc. Software Engineering"),
        ("cyber_security", "B.Sc. Cyber Security"),
    ]
    ROLE_CHOICES = [
        ("student", "Student"),
        ("advisor", "Academic Advisor"),
        ("administrator", "Administrator"),
    ]
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default="student")
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=8, blank=True, null=True)
    otp_expires_at = models.DateTimeField(blank=True, null=True)
    programme = models.CharField(max_length=32, choices=PROGRAMME_CHOICES, default="software_engineering")
    current_level = models.PositiveSmallIntegerField(default=100)
    current_semester = models.PositiveSmallIntegerField(default=1)
    session = models.CharField(max_length=16, default="2025/2026")
    advisor = models.ForeignKey("self", blank=True, null=True, on_delete=models.SET_NULL, related_name="assigned_students", limit_choices_to={"role": "advisor"})
    profile_photo = models.ImageField(upload_to="profile_photos/", blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.email} ({self.role})"
