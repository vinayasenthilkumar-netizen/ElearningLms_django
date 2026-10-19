
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Course, Enrollment, Feedback, BlockedStudent
from .serializers import CourseSerializer, FeedbackInputSerializer


# api view for listing courses
class CourseListAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
    
        profile = getattr(request.user, "profile", None)
 
        role = getattr(profile, "role", None)

        view = request.GET.get("view", "enrolled")

        if role == "STUDENT":
            enrolled_qs = Enrollment.objects.filter(course=OuterRef("pk"), student=request.user)

            if view == "all":

                queryset = (
                    Course.objects.select_related("teacher")
                    .annotate(is_enrolled=Exists(enrolled_qs))
                    .order_by("-created_at")
                )

            else:
             
                queryset = (
                    Course.objects.filter(enrollments__student=request.user)
                    .select_related("teacher")
                    .annotate(is_enrolled=Exists(enrolled_qs))
                    .order_by("-created_at")
                )

        # teacher logic: show only courses taught by this teacher
        elif role == "TEACHER":
            queryset = (
                Course.objects.filter(teacher=request.user)
                .select_related("teacher")
                .order_by("-created_at")
            )
        else:
            # return an empty queryset
            queryset = Course.objects.none()

        serializer = CourseSerializer(queryset, many=True)
        # return the serialized list
        return Response(serializer.data)


# api view for returning one course's details
class CourseDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, course_id):

        course = get_object_or_404(Course.objects.select_related("teacher"), id=course_id)

        serializer = CourseSerializer(course)
        # return the course data
        return Response(serializer.data)


class EnrollCourseAPIView(APIView):
    # require the user to be logged in for this endpoint
    permission_classes = [permissions.IsAuthenticated]

    # handle post requests to enroll in a course
    def post(self, request, course_id):
        # fetch the course or return 404 if it does not exist
        course = get_object_or_404(Course, id=course_id)

        # try to get the user's profile (it may not exist)
        profile = getattr(request.user, "profile", None)
        # read the user's role from the profile
        role = getattr(profile, "role", None)

        # only students are allowed to enroll
        if role != "STUDENT":
            return Response(
                {"detail": "Only students can enroll."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # check if the student is blocked from this course
        blocked = BlockedStudent.objects.filter(course=course, student=request.user).exists()
        if blocked:
            return Response(
                {"detail": "You are blocked from this course."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # create the enrollment if it does not exist already
        enrollment, created = Enrollment.objects.get_or_create(course=course, student=request.user)
        # count how many students are enrolled in this course
        count = Enrollment.objects.filter(course=course).count()

        # return a success response with useful info
        return Response({
            "success": True,
            "created": created,
            "count": count,
            "enrollment_id": enrollment.id,
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


# api view for submitting feedback for a course
class CourseFeedbackAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, course_id):
   
        course = get_object_or_404(Course, id=course_id)

        profile = getattr(request.user, "profile", None)
        # read the user's role from the profile
        role = getattr(profile, "role", None)

        # only students are allowed to leave feedback
        if role != "STUDENT":
            return Response(
                {"detail": "Only students can leave feedback."},
                status=status.HTTP_403_FORBIDDEN,
            )

        is_enrolled = Enrollment.objects.filter(course=course, student=request.user).exists()
        if not is_enrolled:
            return Response(
                {"detail": "You must be enrolled to leave feedback."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = FeedbackInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        feedback, created = Feedback.objects.update_or_create(
            course=course,
            student=request.user,
            defaults={
                "rating": serializer.validated_data["rating"],
                "comment": serializer.validated_data.get("comment", ""),
            },
        )

        # return success data back to the client
        return Response({
            "success": True,
            "created": created,
            "rating": feedback.rating,
            "comment": feedback.comment,
        })