from datetime import timedelta
import random
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import (
    RegisterSerializer,
    OTPVerifySerializer,
    LoginSerializer,
    UserSerializer,
)
from apps.advisories.views import log_activity


def generate_otp():
    return f"{random.randint(100000, 999999)}"


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.otp_code = generate_otp()
        user.otp_expires_at = timezone.now() + timedelta(minutes=15)
        user.save()
        try:
            send_mail("Your TO-AAS verification code", f"Your verification code is {user.otp_code}. It expires in 15 minutes.", settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        except Exception:
            # Development fallback: allows registration when SMTP is deliberately not configured.
            print(f"OTP for {user.email}: {user.otp_code}")
        return Response({"detail": "Registration successful. Verify using OTP sent to email."}, status=status.HTTP_201_CREATED)


class OTPVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        otp_code = serializer.validated_data["otp_code"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.otp_code != otp_code or user.otp_expires_at is None or timezone.now() > user.otp_expires_at:
            return Response({"detail": "OTP is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_email_verified = True
        user.otp_code = None
        user.otp_expires_at = None
        user.save()
        return Response({"detail": "Email verified successfully."})


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            }
        )


class ProfileView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_activity(request.user, "Profile updated", "Personal details edited")
        return Response(serializer.data)
