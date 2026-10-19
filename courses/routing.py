# import re_path so we can define websocket routes using regex paths
from django.urls import re_path

# import the websocket consumers from this app
from . import consumers


# list of websocket url patterns for the courses app
websocket_urlpatterns = [
    # websocket route for a specific course whiteboard using course_id
    re_path(r"ws/whiteboard/(?P<course_id>\d+)/$", consumers.WhiteboardConsumer.as_asgi()),
]