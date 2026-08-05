import os
from unittest import mock

from django.test import SimpleTestCase

from apps.chatbot.views import ChatMessageCreateView


class ChatbotFallbackResponseTests(SimpleTestCase):
    def test_returns_local_advice_when_no_ai_key_is_configured(self):
        view = ChatMessageCreateView()

        # The fallback branch is only reachable with AI_API_KEY unset. Without
        # this patch the test picks up whatever key is in the developer's
        # environment and exercises the live API path instead, so it failed for
        # anyone with a configured key.
        with mock.patch.dict(os.environ, {}, clear=True):
            response = view._call_ai_api({
                "message": "Why was this course recommended?",
                "latest_recommendation": "Your logical reasoning is strong and this course fits your profile.",
            })

        self.assertIn("recommendation", response.lower())
        self.assertIn("logical reasoning", response.lower())
