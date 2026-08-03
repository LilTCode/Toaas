from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import CourseViewSet, TranscriptEntryViewSet

router = DefaultRouter()
router.register(r"course", CourseViewSet, basename="course")
router.register(r"transcript", TranscriptEntryViewSet, basename="transcript")

urlpatterns = [
    path("", include(router.urls)),
]
