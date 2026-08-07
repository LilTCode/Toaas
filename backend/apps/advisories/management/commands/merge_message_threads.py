"""Merge duplicate message threads created before threading was fixed.

Every (student, recipient_type) pair should own exactly one thread. Earlier
versions opened a fresh thread per message, so conversations are scattered
across many rows. This folds each pair's later threads into its earliest one,
preserving chronological order.

Run with --dry-run first to preview.
"""

from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.advisories.models import AdvisorMessage, MessageReply


class Command(BaseCommand):
    help = "Merge split AdvisorMessage threads into one per student/recipient pair."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would change without writing anything.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        groups = defaultdict(list)
        for message in AdvisorMessage.objects.select_related("student").order_by("created_at"):
            groups[(message.student_id, message.recipient_type)].append(message)

        duplicates = {k: v for k, v in groups.items() if len(v) > 1}
        if not duplicates:
            self.stdout.write(self.style.SUCCESS("No split threads found."))
            return

        merged = 0
        moved = 0

        with transaction.atomic():
            for (student_id, recipient_type), threads in duplicates.items():
                keeper, extras = threads[0], threads[1:]

                for extra in extras:
                    # A later thread's opening body was a message in its own
                    # right, so keep it as a student reply on the survivor.
                    if extra.body and not dry_run:
                        reply = MessageReply.objects.create(
                            message=keeper,
                            sender_type="student",
                            sender_name=extra.student.get_full_name() or extra.student.email,
                            content=extra.body,
                        )
                        # created_at is auto_now_add, so restore the real time.
                        MessageReply.objects.filter(pk=reply.pk).update(
                            created_at=extra.created_at
                        )
                    if extra.body:
                        moved += 1

                    if not dry_run:
                        extra.replies.update(message=keeper)
                        extra.delete()

                if not dry_run:
                    keeper.reply_count = keeper.replies.count()
                    keeper.save(update_fields=["reply_count"])

                merged += len(extras)
                self.stdout.write(
                    f"  student={student_id} to={recipient_type}: "
                    f"{len(threads)} threads -> 1 (kept id={keeper.id})"
                )

            if dry_run:
                transaction.set_rollback(True)

        verb = "Would merge" if dry_run else "Merged"
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb} {merged} duplicate threads across {len(duplicates)} "
                f"conversations, moving {moved} messages."
            )
        )
