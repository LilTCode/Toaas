from django.contrib import admin
from .models import CognitiveProfile, Recommendation


@admin.register(CognitiveProfile)
class CognitiveProfileAdmin(admin.ModelAdmin):
    list_display = ["student", "updated_at"]
    readonly_fields = ["updated_at"]


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ["student", "generated_at"]
    readonly_fields = ["generated_at"]
