# import the helper to get the active user model
from django.contrib.auth import get_user_model

from django.contrib.auth.models import Group

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import Group
from .models import Notification
from .models import Profile, StatusUpdate

TEST_CHANNEL_LAYERS = {

    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}


# override channel layers setting for this test class
@override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS)

class StatusUpdateViewTests(TestCase):
    # setup runs before each test method
    def setUp(self):
        # get the user model for creating test users
        User = get_user_model()
        # make sure the teachers group exists
        teachers_group, _ = Group.objects.get_or_create(name="Teachers")
        # make sure the students group exists
        students_group, _ = Group.objects.get_or_create(name="Students")

        # create a student user for testing
        self.student = User.objects.create_user(

            username="student1",

            password="testpass123",

            first_name="Student",

            last_name="One",

            email="student1@example.com",
        )
        # set the student's profile role to student
        self.student.profile.role = Profile.Role.STUDENT
        # save the student's profile changes
        self.student.profile.save()

        # create a teacher user for testing
        self.teacher = User.objects.create_user(

            username="teacher1",
            password="testpass123",
            first_name="Teacher",
            last_name="One",
            email="teacher1@example.com",
        )
        # set the teacher's profile role to teacher
        self.teacher.profile.role = Profile.Role.TEACHER
        # save the teacher's profile changes
        self.teacher.profile.save()
        self.teacher.groups.add(teachers_group)
        self.teacher.groups.remove(students_group)

    # test that a student can create a status update
    def test_student_can_create_status_update(self):
        # log in as the student user
        self.client.login(username="student1", password="testpass123")

        # send a post request to create a new status update
        response = self.client.post(reverse("status_create"), {
            # the status update text to submit
            "content": "This is my test status update."
        })

        # make sure the view redirects after success
        self.assertEqual(response.status_code, 302)
        # make sure one status update was created for this student
        self.assertEqual(StatusUpdate.objects.filter(user=self.student).count(), 1)
        # make sure the saved content matches what we posted
        self.assertEqual(
            # get the saved status update content
            StatusUpdate.objects.get(user=self.student).content,
            # expected content text
            "This is my test status update."
        )

    # test that a teacher cannot create a status update
    def test_teacher_cannot_create_status_update(self):
        # log in as the teacher user
        self.client.login(username="teacher1", password="testpass123")

        # try to post a status update as a teacher
        response = self.client.post(reverse("status_create"), {
            # the status update text to submit
            "content": "Teachers should not post statuses here."
        })


        self.assertEqual(response.status_code, 403)

        self.assertEqual(StatusUpdate.objects.count(), 0)


@override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS)
# tests for the accounts api endpoints
class AccountsApiTests(TestCase):
    # setup runs before each test method
    def setUp(self):
        User = get_user_model()
 
        self.api = APIClient()

        Group.objects.get_or_create(name="Teachers")

        Group.objects.get_or_create(name="Students")

        # create a student user for api tests
        self.student = User.objects.create_user(
            
            username="studentapi",         
            password="testpass123",         
            first_name="API",          
            last_name="Student",           
            email="studentapi@example.com",
        )
        # set the role to student
        self.student.profile.role = Profile.Role.STUDENT
        # bio
        self.student.profile.bio = "Original bio"
        # save changes
        self.student.profile.save()

    # test the api me endpoint returns user info
    def test_api_get_me(self):
        self.api.force_authenticate(user=self.student)
 
        response = self.api.get(reverse("api-me"))

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data["username"], "studentapi")

        self.assertEqual(response.data["role"], "STUDENT")

    # test that posting a status works through the api
    def test_api_post_status(self):
        # authenticate the api client as the student
        self.api.force_authenticate(user=self.student)

        # send a post request to create a status update
        response = self.api.post(reverse("api-status"), {

            "content": "Posted through the API"
        }, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(StatusUpdate.objects.filter(user=self.student).count(), 1)
        # make sure the content matches
        self.assertEqual(
            # read back the saved content
            StatusUpdate.objects.get(user=self.student).content,

            "Posted through the API"
        )

    # test that putting to me updates user and profile data
    def test_api_put_me_updates_profile(self):
    
        self.api.force_authenticate(user=self.student)

        # send a put request to update user and bio
        response = self.api.put(reverse("api-me"), {

            "first_name": "Updated",

            "last_name": "Name",

            "email": "updated@example.com",
            "bio": "Updated through API",
        }, format="json")

        # make sure the response is ok
        self.assertEqual(response.status_code, 200)

        # refresh the user from the database
        self.student.refresh_from_db()

        self.student.profile.refresh_from_db()

        # check the first name saved correctly
        self.assertEqual(self.student.first_name, "Updated")
        self.assertEqual(self.student.last_name, "Name")
        self.assertEqual(self.student.email, "updated@example.com")
        self.assertEqual(self.student.profile.bio, "Updated through API")


@override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS)
# tests for edge cases and permission checks
class AccountsEdgeCaseTests(TestCase):
    # setup runs before each test method
    def setUp(self):
        # get the user model for creating test users
        User = get_user_model()
        # create a drf api client for requests
        self.api = APIClient()

        teachers_group, _ = Group.objects.get_or_create(name="Teachers")
        students_group, _ = Group.objects.get_or_create(name="Students")

        # create a student user for edge case tests
        self.student = User.objects.create_user(

            username="edge_student",
            password="testpass123",
            email="edge_student@example.com",
        )

        self.student.profile.role = Profile.Role.STUDENT
        self.student.profile.save()

        # create a teacher user for edge case tests
        self.teacher = User.objects.create_user(
            username="edge_teacher",
            password="testpass123",
            email="edge_teacher@example.com",
        )
        # set the role to teacher
        self.teacher.profile.role = Profile.Role.TEACHER
        self.teacher.profile.save()
        self.teacher.groups.add(teachers_group)
        self.teacher.groups.remove(students_group)

        # create a notification for the student
        self.note = Notification.objects.create(
            # set the owner of the notification
            user=self.student,
            title="Test Notification",

            message="Test message",
        )

    # test that the me endpoint requires login
    def test_api_me_requires_auth(self):
        # call the endpoint without authenticating
        response = self.api.get(reverse("api-me"))
        # allow either 401 or 403 depending on auth setup
        self.assertIn(response.status_code, [401, 403])

    # test that a teacher cannot post status updates via api
    def test_teacher_cannot_post_status_via_api(self):
    
        self.api.force_authenticate(user=self.teacher)

        # try posting a status update as a teacher
        response = self.api.post(reverse("api-status"), {
            # status content for the api request
            "content": "Teacher status via API"
        }, format="json")

        self.assertEqual(response.status_code, 403)
        # make sure no status updates were created
        self.assertEqual(StatusUpdate.objects.count(), 0)

    # test that another user cannot mark someone else's notification as read
    def test_notification_cannot_be_marked_read_by_other_user(self):

        self.api.force_authenticate(user=self.teacher)

        # try to mark the student's notification as read
        response = self.api.post(

            reverse("api-notification-read", args=[self.note.id]),
          
            {},
          
            format="json"
        )

  
        self.assertEqual(response.status_code, 404)
   
        self.note.refresh_from_db()
      
        self.assertFalse(self.note.is_read)

    # test that the signal creates a profile and assigns students group
    def test_signal_creates_profile_and_students_group(self):
        User = get_user_model()

        # create a brand new user to trigger the signal
        fresh_user = User.objects.create_user(
            username="fresh_user",
            password="testpass123",
            email="fresh_user@example.com",
        )

        # make sure the user now has a profile attribute
        self.assertTrue(hasattr(fresh_user, "profile"))
        # make sure the default role is student
        self.assertEqual(fresh_user.profile.role, Profile.Role.STUDENT)
        # make sure the user was added to the students group
        self.assertTrue(fresh_user.groups.filter(name="Students").exists())