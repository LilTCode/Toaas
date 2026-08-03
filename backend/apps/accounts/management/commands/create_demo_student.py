from django.core.management.base import BaseCommand
from apps.accounts.models import User


class Command(BaseCommand):
    help = "Create a demo student account for local development"

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            email="student@demo.edu",
            defaults={
                "username": "demo-student",
                "role": "student",
                "first_name": "Demo",
                "last_name": "Student",
                "is_email_verified": True,
                "is_active": True,
            },
        )
        if created:
            user.set_password("demo1234")
            user.save()
            self.stdout.write(self.style.SUCCESS("Created demo student account."))
        else:
            user.set_password("demo1234")
            user.is_email_verified = True
            user.is_active = True
            user.save()
            self.stdout.write(self.style.SUCCESS("Updated demo student account."))
