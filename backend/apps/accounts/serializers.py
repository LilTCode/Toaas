from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth import authenticate
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role", "is_email_verified", "programme", "current_level", "current_semester", "session", "profile_photo", "advisor"]
        read_only_fields = ["is_email_verified", "role", "advisor"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "password", "role", "first_name", "last_name", "programme", "current_level", "current_semester"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = True
        user.save()
        return user


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=8)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs.get("email"), password=attrs.get("password"))
        if user is None:
            raise serializers.ValidationError("Invalid credentials")
        if not user.is_email_verified:
            raise serializers.ValidationError("Email is not verified")
        attrs["user"] = user
        return attrs
