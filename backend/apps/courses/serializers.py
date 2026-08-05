from rest_framework import serializers
from .models import Course, TranscriptEntry


class CourseSerializer(serializers.ModelSerializer):
    prerequisites = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "code",
            "title",
            "credit_units",
            "semester",
            "level",
            "prerequisites",
            "description",
            "learning_objectives",
            "major_topics",
            "recommended_references",
            "department_classification",
            "is_compulsory",
            "is_active",
            "metadata",
            "abstract_reasoning",
            "logical_reasoning",
            "theoretical_knowledge",
            "quantitative_calculation",
            "practical_application",
        ]
        read_only_fields = ["prerequisites"]


class TranscriptEntrySerializer(serializers.ModelSerializer):
    student = serializers.StringRelatedField(read_only=True)
    course = CourseSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), source="course", write_only=True)

    class Meta:
        model = TranscriptEntry
        fields = ["id", "student", "course", "course_id", "semester", "grade", "credit_points", "status"]
        read_only_fields = ["status"]

    def validate_grade(self, value):
        return value.upper()

    def create(self, validated_data):
        grade = validated_data.get("grade", "")
        validated_data["status"] = "failed" if grade == "F" else "passed"
        return super().create(validated_data)

    def update(self, instance, validated_data):
        grade = validated_data.get("grade", instance.grade)
        validated_data["status"] = "failed" if grade == "F" else "passed"
        return super().update(instance, validated_data)
