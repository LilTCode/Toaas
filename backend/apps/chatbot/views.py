import os
import ssl
import certifi
import requests
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ChatConversation, ChatMessage
from .serializers import ChatConversationSerializer, ChatMessageSerializer
from apps.advisories.models import Recommendation
from apps.advisories.views import log_activity


class ChatConversationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        conversations = ChatConversation.objects.filter(student=request.user).order_by("-updated_at")
        serializer = ChatConversationSerializer(conversations, many=True)
        return Response(serializer.data)


class ChatConversationCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        conversation = ChatConversation.objects.create(student=request.user)
        serializer = ChatConversationSerializer(conversation)
        return Response(serializer.data)


class ChatMessageCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, conversation_id):
        try:
            conversation = ChatConversation.objects.get(id=conversation_id, student=request.user)
        except ChatConversation.DoesNotExist:
            return Response({"detail": "Conversation not found."}, status=404)

        message = ChatMessage.objects.create(
            conversation=conversation,
            sender_role="student",
            content=request.data.get("content", ""),
        )

        # Build structured context from recommendations and academic state
        recommendation = Recommendation.objects.filter(student=request.user).order_by("-generated_at").first()
        context = {
            "student_email": request.user.email,
            "latest_recommendation": recommendation.explanation if recommendation else "No recommendations available.",
            "message": message.content,
        }

        # Placeholder for AI integration
        ai_response = self._call_ai_api(context)
        ChatMessage.objects.create(
            conversation=conversation,
            sender_role="system",
            content=ai_response,
        )

        conversation.save()
        log_activity(request.user, "Chatted with AI assistant", f"Asked: {message.content[:60]}...")
        return Response({"response": ai_response})

    def _call_ai_api(self, context):
        api_key = os.getenv("AI_API_KEY")
        if not api_key:
            message = (context.get("message") or "").strip()
            recommendation = context.get("latest_recommendation") or "No recommendation available."

            if "recommend" in message.lower() or "why" in message.lower() or "course" in message.lower():
                return (
                    "Based on your current academic profile, this recommendation was suggested because it fits your strengths and study pattern. "
                    f"The advisory system notes: {recommendation} "
                    "You can also review your transcript and cognitive profile to understand why it was prioritized."
                )

            if "prereq" in message.lower() or "prerequisite" in message.lower():
                return "Please review the course prerequisites listed in the recommendation card and compare them with your completed modules before registering."

            if "carry" in message.lower() or "semester" in message.lower():
                return "For semester planning, focus on completing your outstanding and prerequisite-heavy courses first so your workload stays balanced."

            return (
                "I’m operating in demo mode right now, so I’m using the advisory context already stored in the system. "
                f"Your latest recommendation summary is: {recommendation}"
            )

        payload = {
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "instructions": (
                "You are a careful academic advisory assistant. Explain the provided "
                "recommendation, prerequisites, course-load policy, and study planning in "
                "clear language. Do not invent university rules, grades, or course data. "
                "Encourage the student to confirm final registration choices with their advisor."
            ),
            "input": f"Student question: {context['message']}\n\nLatest recommendation: {context['latest_recommendation']}",
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(
                os.getenv("AI_API_URL", "https://api.openai.com/v1/responses"),
                json=payload,
                headers=headers,
                timeout=30,
                verify=certifi.where(),
            )
            response.raise_for_status()
            return response.json().get("output_text", "I could not generate an academic response right now.")
        except requests.RequestException:
            return "The AI service is temporarily unavailable. Please try again shortly."
