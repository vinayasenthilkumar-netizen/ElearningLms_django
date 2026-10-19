# import json so we can read and send data as json text
import json

# import the sync websocket consumer class (not async)
from channels.generic.websocket import WebsocketConsumer

# import a helper so we can call async channel methods from sync code
from asgiref.sync import async_to_sync

# import anonymous user for safety if user is missing in scope
from django.contrib.auth.models import AnonymousUser

# import course and enrollment models to check access to the whiteboard
from .models import Course, Enrollment


# websocket consumer for the live course whiteboard
class WhiteboardConsumer(WebsocketConsumer):

    # runs when a websocket client tries to connect
    def connect(self):

        user = self.scope.get("user", AnonymousUser())

        self.course_id = self.scope["url_route"]["kwargs"]["course_id"]

        if not user.is_authenticated:
            self.close()
            return

        try:
            course = Course.objects.get(id=self.course_id)

        except Course.DoesNotExist:
            self.close()
            return

        is_teacher = user == course.teacher

        is_enrolled = Enrollment.objects.filter(course=course, student=user).exists()


        if not (is_teacher or is_enrolled):
            self.close()
            return

        # set the group name for this course whiteboard
        self.room_group_name = f"whiteboard_course_{self.course_id}"

        # add this websocket connection to the whiteboard group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        # accept the websocket connection
        self.accept()

    # runs when the websocket disconnects
    def disconnect(self, close_code):
        # only try to discard if the group name was set
        if hasattr(self, "room_group_name"):
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
            )

    # runs when the server receives a message from the websocket client
    def receive(self, text_data):
        # parse the incoming json string
        data = json.loads(text_data)

        # broadcast the event data to everyone in the same whiteboard room
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                # this event name must match the method below
                "type": "whiteboard_event",
                # send the event type (draw or clear)
                "event": data.get("event"),
                # send starting x
                "x0": data.get("x0"),
                # send starting y
                "y0": data.get("y0"),
                # send ending x
                "x1": data.get("x1"),
                # send ending y
                "y1": data.get("y1"),
                # send color
                "color": data.get("color"),
                # send brush size
                "size": data.get("size"),
            }
        )

    # runs when the group sends a whiteboard event
    def whiteboard_event(self, event):
        # send the event back to the websocket as json
        self.send(text_data=json.dumps(event))