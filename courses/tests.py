# import timedelta so we can create time offsets like now - 1 hour
from datetime import timedelta

# import helper to get the active user model
from django.contrib.auth import get_user_model

# import groups so we can assign users to teachers/students groups
from django.contrib.auth.models import Group

# import django test tools and a helper to override settings during tests
from django.test import TestCase, override_settings

# import reverse so we can build urls from named routes
from django.urls import reverse

# import timezone so we can create past/future due dates
from django.utils import timezone

# import drf api client for testing api endpoints
from rest_framework.test import APIClient

# import account models used in these tests
from accounts.models import Profile, Notification

# import course models used in these tests
from .models import Course, Enrollment, Feedback, Assignment


# test channel layers config so channels uses an in-memory backend
TEST_CHANNEL_LAYERS = {
    # name
    "default": {
        # use the in-memory channel layer for testing
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}



@override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS)

class CourseFlowTests(TestCase):

    def setUp(self):

        User = get_user_model()

        # make sure the teachers group exists
        teachers_group, _ = Group.objects.get_or_create(name="Teachers")
        # make sure the students group exists
        students_group, _ = Group.objects.get_or_create(name="Students")

        # create a teacher user for course tests
        self.teacher = User.objects.create_user(
 
            username="teacher_course",
 
            password="testpass123",

            email="teacher_course@example.com",
        )
        # set role to teacher
        self.teacher.profile.role = Profile.Role.TEACHER
        # save profile changes
        self.teacher.profile.save()
        # add teacher to teachers group
        self.teacher.groups.add(teachers_group)
        # remove teacher from students group
        self.teacher.groups.remove(students_group)

        # create a student user for course tests
        self.student = User.objects.create_user(
            # student username
            username="student_course",
            # student password
            password="testpass123",
            # student email
            email="student_course@example.com",
        )
        # set role to student
        self.student.profile.role = Profile.Role.STUDENT
        # save profile changes
        self.student.profile.save()

        # create a course owned by the teacher
        self.course = Course.objects.create(
            # set course teacher
            teacher=self.teacher,
            # set course title
            title="Advanced Web Development",
            # set course description
            description="Test course",
        )

    # test that a student can enroll and teacher gets notified
    def test_student_can_enroll_and_teacher_gets_notification(self):
    
        self.client.login(username="student_course", password="testpass123")

      
        response = self.client.post(
         
            reverse("courses:enroll", args=[self.course.id]),
       
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )

        # expect success response
        self.assertEqual(response.status_code, 200)
        # make sure the enrollment was created
        self.assertEqual(Enrollment.objects.filter(course=self.course, student=self.student).count(), 1)
        # make sure the teacher got the enrollment notification
        self.assertEqual(Notification.objects.filter(user=self.teacher, title="New course enrollment").count(), 1)

    # test that a student can leave feedback and teacher gets notified
    def test_student_can_leave_feedback_and_teacher_gets_notification(self):
        # enroll the student first
        Enrollment.objects.create(course=self.course, student=self.student)
        # log in as the student
        self.client.login(username="student_course", password="testpass123")

        # send feedback request as ajax
        response = self.client.post(
            # feedback submit url
            reverse("courses:feedback_submit", args=[self.course.id]),
            {
             
                "rating": 5,
               
                "comment": "Great course",
            },
            # set ajax header
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )

        # expect success response
        self.assertEqual(response.status_code, 200)
        # make sure feedback was created
        self.assertEqual(Feedback.objects.filter(course=self.course, student=self.student).count(), 1)
        # make sure teacher got a notification
        self.assertEqual(Notification.objects.filter(user=self.teacher).count(), 1)

    # test that submissions are blocked when  deadline is passed
    def test_submission_is_locked_after_deadline(self):
      
        Enrollment.objects.create(course=self.course, student=self.student)

        # create an assignment with a past due date
        assignment = Assignment.objects.create(
    
            course=self.course,
            title="Past Due Assignment",
            instructions="Too late",
            due_date=timezone.now() - timedelta(hours=1),
        )

        # log in as the student
        self.client.login(username="student_course", password="testpass123")

        # try to upload a submission
        response = self.client.post(
            reverse("courses:submission_upload", args=[self.course.id, assignment.id]),
            # empty post body
            {}
        )

        # expect forbidden because deadline passed
        self.assertEqual(response.status_code, 403)


# override channel layers setting for this test class
@override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS)
# tests for the courses api endpoints
class CourseApiTests(TestCase):
    # setup runs before each test method
    def setUp(self):
  
        User = get_user_model()
  
        self.api = APIClient()

        # make sure the teachers group exists
        teachers_group, _ = Group.objects.get_or_create(name="Teachers")
        # make sure the students group exists
        students_group, _ = Group.objects.get_or_create(name="Students")

        # create a teacher user for api tests
        self.teacher = User.objects.create_user(

            username="teacher_api",

            password="testpass123",

            email="teacher_api@example.com",
        )
        # set role to teacher
        self.teacher.profile.role = Profile.Role.TEACHER
        # save profile changes
        self.teacher.profile.save()
        # add teacher to teachers group
        self.teacher.groups.add(teachers_group)
        # remove teacher from students group
        self.teacher.groups.remove(students_group)

        # create a student user for api tests
        self.student = User.objects.create_user(

            username="student_api",
     
            password="testpass123",

            email="student_api@example.com",
        )
        # set role to student
        self.student.profile.role = Profile.Role.STUDENT
        # save profile changes
        self.student.profile.save()

        # create a course owned by the teacher
        self.course = Course.objects.create(
      
            teacher=self.teacher,
          
            title="API Course",
         
            description="API test course",
        )

    # test that the courses list api works
    def test_api_get_courses(self):
        # authenticate as the teacher
        self.api.force_authenticate(user=self.teacher)

        # get the courses list
        response = self.api.get(reverse("api-courses"))

        # expect success response
        self.assertEqual(response.status_code, 200)
        # expect one course
        self.assertEqual(len(response.data), 1)
        # check the course title
        self.assertEqual(response.data[0]["title"], "API Course")

    # test enrolling through the api
    def test_api_post_enroll(self):
     
        self.api.force_authenticate(user=self.student)

        # post to enroll endpoint
        response = self.api.post(
          
            reverse("api-course-enroll", args=[self.course.id]),
         
            {},
          
            format="json"
        )

        # status can be 200 already enrolled or 201 created
        self.assertIn(response.status_code, [200, 201])
        # make sure enrollment exists
        self.assertEqual(Enrollment.objects.filter(course=self.course, student=self.student).count(), 1)

    # test leaving feedback through the api
    def test_api_post_feedback(self):
    
        Enrollment.objects.create(course=self.course, student=self.student)
    
        self.api.force_authenticate(user=self.student)

        # post to feedback endpoint
        response = self.api.post(
       
            reverse("api-course-feedback", args=[self.course.id]),
            {
               
                "rating": 4,
               
                "comment": "Good through API",
            },
            # send json format
            format="json"
        )

        # expect success response
        self.assertEqual(response.status_code, 200)
        # make sure feedback exists
        self.assertEqual(Feedback.objects.filter(course=self.course, student=self.student).count(), 1)
        # check rating saved correctly
        self.assertEqual(Feedback.objects.get(course=self.course, student=self.student).rating, 4)



@override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS)
# tests for edge cases and permission checks
class CourseEdgeCaseTests(TestCase):
    # setup runs before each test method
    def setUp(self):
    
        User = get_user_model()
     
        self.api = APIClient()

        # make sure the teachers group exists
        teachers_group, _ = Group.objects.get_or_create(name="Teachers")
        # make sure the students group exists
        students_group, _ = Group.objects.get_or_create(name="Students")

        # create a teacher user for edge case tests
        self.teacher = User.objects.create_user(
          
            username="edge_teacher_course",
          
            password="testpass123",
          
            email="edge_teacher_course@example.com",
        )
   
        self.teacher.profile.role = Profile.Role.TEACHER
     
        self.teacher.profile.save()
    
        self.teacher.groups.add(teachers_group)
    
        self.teacher.groups.remove(students_group)

        # create a student user for edge case tests
        self.student = User.objects.create_user(
    
            username="edge_student_course",
     
            password="testpass123",

            email="edge_student_course@example.com",
        )
        # set role to student
        self.student.profile.role = Profile.Role.STUDENT
        # save profile changes
        self.student.profile.save()

        # create a course owned by the teacher
        self.course = Course.objects.create(
            # set course teacher
            teacher=self.teacher,
            # set course title
            title="Edge Test Course",
            # set course description
            description="Edge cases",
        )

    # test that a teacher cannot enroll via api
    def test_teacher_cannot_enroll_via_api(self):
        # authenticate as the teacher
        self.api.force_authenticate(user=self.teacher)

        # try to enroll as a teacher
        response = self.api.post(
     
            reverse("api-course-enroll", args=[self.course.id]),
        
            {},
          
            format="json"
        )

        # expect forbidden
        self.assertEqual(response.status_code, 403)
        # make sure no enrollments exist
        self.assertEqual(Enrollment.objects.count(), 0)

    # test that a student who is not enrolled cannot leave feedback
    def test_student_not_enrolled_cannot_leave_feedback_via_api(self):
        # authenticate as the student
        self.api.force_authenticate(user=self.student)

        # try to leave feedback without enrollment
        response = self.api.post(
            # feedback url
            reverse("api-course-feedback", args=[self.course.id]),
            {
                # rating value
                "rating": 5,
                # comment text
                "comment": "Should fail",
            },
            # send json format
            format="json"
        )

        # expect forbidden
        self.assertEqual(response.status_code, 403)
        # make sure no feedback exists
        self.assertEqual(Feedback.objects.count(), 0)

    # test that duplicate enroll does not create a second record
    def test_duplicate_enroll_does_not_create_second_enrollment(self):

        Enrollment.objects.create(course=self.course, student=self.student)
  
        self.api.force_authenticate(user=self.student)

        # enroll again through the api
        response = self.api.post(

            reverse("api-course-enroll", args=[self.course.id]),

            {},
   
            format="json"
        )

        # status can be 200 or 201 
        self.assertIn(response.status_code, [200, 201])
        # still only one enrollment should exist
        self.assertEqual(
            Enrollment.objects.filter(course=self.course, student=self.student).count(),
            1
        )

    # test that an invalid rating is rejected
    def test_invalid_feedback_rating_is_rejected(self):
        # enroll the student first
        Enrollment.objects.create(course=self.course, student=self.student)
        # authenticate as the student
        self.api.force_authenticate(user=self.student)

        # try to send an invalid rating
        response = self.api.post(

            reverse("api-course-feedback", args=[self.course.id]),
            {
    
                "rating": 6,

                "comment": "Too high",
            },
            # send json format
            format="json"
        )

        # expect bad request
        self.assertEqual(response.status_code, 400)
        # make sure no feedback was saved
        self.assertEqual(Feedback.objects.count(), 0)