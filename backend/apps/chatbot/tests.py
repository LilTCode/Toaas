from django.test import SimpleTestCase

from apps.chatbot.views import ChatMessageCreateView


class ChatbotFallbackResponseTests(SimpleTestCase):
    def test_returns_local_advice_when_no_ai_key_is_configured(self):
        view = ChatMessageCreateView()
        response = view._call_ai_api({
            "message": "Why was this course recommended?",
            "latest_recommendation": "Your logical reasoning is strong and this course fits your profile.",
        })

        self.assertIn("recommendation", response.lower())
        self.assertIn("logical reasoning", response.lower())
