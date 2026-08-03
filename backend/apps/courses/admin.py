from django.contrib import admin
from .models import Course, TranscriptEntry


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["code", "title", "level", "semester", "department_classification"]
    search_fields = ["code", "title"]
    filter_horizontal = ["prerequisites"]


@admin.register(TranscriptEntry)
class TranscriptEntryAdmin(admin.ModelAdmin):
    list_display = ["student", "course", "semester", "status", "grade"]
    list_filter = ["status", "semester"]
    search_fields = ["student__email", "course__code"]
