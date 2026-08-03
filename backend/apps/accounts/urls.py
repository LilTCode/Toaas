from django.urls import path
from .views import RegisterView, OTPVerifyView, LoginView, ProfileView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-otp/", OTPVerifyView.as_view(), name="verify-otp"),
    path("login/", LoginView.as_view(), name="login"),
    path("profile/", ProfileView.as_view(), name="profile"),
]
