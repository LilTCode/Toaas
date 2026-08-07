from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.advisories.models import AdvisorMessage, MessageReply


class StaffSendMessageTests(TestCase):
    """An advisor's outgoing message must be attributed to the advisor and land
    in the student's existing thread, not appear as the student's own words in a
    brand-new thread."""

    def setUp(self):
        self.client = APIClient()
        self.student = User.objects.create_user(
            username="STU001", email="stu@test.edu", password="pw", role="student"
        )
        self.advisor = User.objects.create_user(
            username="ADV001", email="adv@test.edu", password="pw",
            role="advisor", first_name="Ada", last_name="Lovelace",
        )

    def _send(self, body="Please register CSC 308."):
        self.client.force_authenticate(self.advisor)
        return self.client.post(
            reverse("staff-send-message"),
            {"student_id": self.student.id, "body": body},
            format="json",
        )

    def test_message_is_attributed_to_staff_not_student(self):
        response = self._send()
        self.assertEqual(response.status_code, 201)

        reply = MessageReply.objects.get()
        self.assertEqual(reply.sender_type, "staff")
        self.assertIn("Ada Lovelace", reply.sender_name)
        self.assertEqual(reply.content, "Please register CSC 308.")

    def test_reuses_existing_thread_instead_of_creating_a_new_one(self):
        thread = AdvisorMessage.objects.create(
            student=self.student, recipient_type="advisor",
            subject="Course plan", body="Which electives should I take?",
        )

        self._send()

        self.assertEqual(AdvisorMessage.objects.count(), 1)
        self.assertEqual(MessageReply.objects.get().message_id, thread.id)

    def test_never_overwrites_the_students_opening_message(self):
        thread = AdvisorMessage.objects.create(
            student=self.student, recipient_type="advisor",
            subject="Course plan", body="Which electives should I take?",
        )

        self._send()

        thread.refresh_from_db()
        self.assertEqual(thread.body, "Which electives should I take?")

    def test_creates_a_thread_when_the_student_has_none(self):
        response = self._send()

        self.assertEqual(response.status_code, 201)
        thread = AdvisorMessage.objects.get()
        # Empty body: the advisor opened the conversation, so there is no
        # student message to show above the advisor's own.
        self.assertEqual(thread.body, "")
        self.assertEqual(thread.replies.get().sender_type, "staff")

    def test_students_cannot_send_as_staff(self):
        self.client.force_authenticate(self.student)
        response = self.client.post(
            reverse("staff-send-message"),
            {"student_id": self.student.id, "body": "hello"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)


class StudentMessageThreadingTests(TestCase):
    """A student writing to the same recipient repeatedly should build one
    conversation, not a new thread per message."""

    def setUp(self):
        self.client = APIClient()
        self.student = User.objects.create_user(
            username="STU002", email="stu2@test.edu", password="pw", role="student"
        )
        self.client.force_authenticate(self.student)

    def _send(self, body, recipient_type="advisor"):
        return self.client.post(
            reverse("advisor-message-list"),
            {"recipient_type": recipient_type, "subject": "Course plan", "body": body},
            format="json",
        )

    def test_second_message_appends_to_the_same_thread(self):
        self._send("Good afternoon sir")
        self._send("How are you doing?")

        self.assertEqual(AdvisorMessage.objects.count(), 1)
        thread = AdvisorMessage.objects.get()
        self.assertEqual(thread.body, "Good afternoon sir")
        replies = list(thread.replies.all())
        self.assertEqual(len(replies), 1)
        self.assertEqual(replies[0].content, "How are you doing?")
        self.assertEqual(replies[0].sender_type, "student")

    def test_different_recipients_get_separate_threads(self):
        self._send("For my advisor", recipient_type="advisor")
        self._send("For the office", recipient_type="administrator")

        self.assertEqual(AdvisorMessage.objects.count(), 2)

    def test_response_returns_the_full_thread(self):
        self._send("First")
        response = self._send("Second")

        self.assertEqual(response.status_code, 201)
        # The client renders straight from this payload, so it must carry the
        # whole thread rather than just the newly created reply.
        self.assertEqual(response.data["body"], "First")
        self.assertEqual(len(response.data["replies"]), 1)
