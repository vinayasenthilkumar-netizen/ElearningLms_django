
from django.urls import re_path

# import the websocket consumers 
from . import consumers


# list of websocket url patterns for the chat app
websocket_urlpatterns = [
    # websocket route for a specific course chat room using course_id
    re_path(r"ws/chat/(?P<course_id>\d+)/$", consumers.ChatConsumer.as_asgi()),
]