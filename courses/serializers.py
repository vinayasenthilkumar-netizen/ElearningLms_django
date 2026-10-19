# import rest framework serializers to convert models to json and validate input
from rest_framework import serializers

# import the course model used by the course serializer
from .models import Course


# serializer that returns course data for the api
class CourseSerializer(serializers.ModelSerializer):

    teacher_username = serializers.CharField(source="teacher.username", read_only=True)

    is_enrolled = serializers.BooleanField(read_only=True, required=False)


    class Meta:
        # connect this serializer to the course model
        model = Course
        # fields included in the api response
        fields = ["id", "title", "description", "teacher_username", "created_at", "is_enrolled"]


# serializer for validating feedback input data 
class FeedbackInputSerializer(serializers.Serializer):
    # rating number between 1 and 5
    rating = serializers.IntegerField(min_value=1, max_value=5)
    # optional comment text
    comment = serializers.CharField(required=False, allow_blank=True)