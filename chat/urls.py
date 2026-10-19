
from django.urls import path
from . import views


# set the app namespace for these urls (used like chat:room)
app_name = "chat"


# list of url patterns for the chat app
urlpatterns = [
    # route for the chat room page for a specific course
    path("course/<int:course_id>/", views.room, name="room"),
]