# import json so we can read and send data as json text
import json
# import the sync websocket consumer class
from channels.generic.websocket import WebsocketConsumer
# import a helper so we can call async channel methods from sync code
from asgiref.sync import async_to_sync
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from courses.models import Course, Enrollment
from .models import ChatMessage
from django.urls import reverse
from accounts.utils import create_notification


# websocket consumer for course chat rooms
class ChatConsumer(WebsocketConsumer):

    # runs when a websocket client tries to connect
    def connect(self):

        user = self.scope.get("user", AnonymousUser())
        # read the course id from the url route
        self.course_id = self.scope["url_route"]["kwargs"]["course_id"]
        # if the user is not logged in, close the connection
        if not user.is_authenticated:
            self.close()
            return

        # try load the course from the database
        try:
            course = Course.objects.get(id=self.course_id)
        # if the course does not exist close the connection
        except Course.DoesNotExist:
            self.close()
            return
        is_teacher = user == course.teacher
        is_enrolled = Enrollment.objects.filter(course=course, student=user).exists()
        if not (is_teacher or is_enrolled):
            self.close()
            return

        # set the group name for this course chat room
        self.room_group_name = f"chat_course_{self.course_id}"

        # add this websocket connection to the course chat group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        # accept the websocket connection
        self.accept()

    # runs when the websocket disconnects
    def disconnect(self, close_code):

        if hasattr(self, "room_group_name"):
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
            )

    # runs when the server receives a message from the websocket client
    def receive(self, text_data):
        user = self.scope["user"]
        data = json.loads(text_data)
        message = (data.get("message") or "").strip()

        if not message:
            return

        course = Course.objects.get(id=self.course_id)

        chat_message = ChatMessage.objects.create(
            course=course,
            sender=user,
            message=message,
        )

        
        # build the link to the chat room page
        chat_link = reverse("chat:room", args=[course.id])

        # notify the teacher if the sender is not the teacher
        if user != course.teacher:
            create_notification(
                user=course.teacher,
                title="New chat message",
                message=f"{user.username}: {chat_message.message[:60]}",
                course=course,
                link=chat_link,
            )

        # get all enrollments for this course (students)
        enrollments = Enrollment.objects.filter(course=course).select_related("student")

        # loop through each enrolled student
        for enrollment in enrollments:
            # skip the sender so they don’t notify themselves
            if enrollment.student == user:
                continue

            # create a notification for the student
            create_notification(
                user=enrollment.student,
                title="New chat message",
                message=f"{user.username}: {chat_message.message[:60]}",
                course=course,
                link=chat_link,
            )




        # send the message to everyone in the course chat group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": chat_message.message,
                "sender": user.username,
                "created_at": timezone.localtime(chat_message.created_at).strftime("%b %d, %Y %H:%M"),
            }
        )

    # runs when the group sends a "chat_message" event
    def chat_message(self, event):
        # send the message data back to the websocket as json
        self.send(text_data=json.dumps({
            # message text sent to the client
            "message": event["message"],
            # sender username sent to the client
            "sender": event["sender"],
            # created time string sent to the client
            "created_at": event["created_at"],
        }))