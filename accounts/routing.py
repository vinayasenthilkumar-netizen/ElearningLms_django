# import re_path so we can define websocket routes using regex paths
from django.urls import re_path

# import the websocket consumers from this app
from . import wsconsumers


# list of websocket url patterns for django channels
websocket_urlpatterns = [
    # route for notifications websocket connection
    re_path(r"ws/notifications/$", wsconsumers.NotificationConsumer.as_asgi()),
]