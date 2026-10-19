
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification


# create a notification for a user and optionally push it over websockets
def create_notification(user, title, message="", course=None, link=""):
    # create and save the notification in the database
    note = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        course=course,
        link=link,
    )

    # get the active channel layer (used for websockets)
    channel_layer = get_channel_layer()

    # only try to send a websocket message if channels is set up
    if channel_layer:
        # send a message to the user's group so their page can update live
        async_to_sync(channel_layer.group_send)(
            # this group name must match what your consumer uses
            f"user_{user.id}",   # must match NotificationConsumer.connect()
            # this is the event data sent to the consumer
            {
                "type": "notification_message",   # must match NotificationConsumer.notification_message()
                "id": note.id,
                "title": note.title,
                "message": note.message,
                "created_at": timezone.localtime(note.created_at).strftime("%b %d, %Y %H:%M"),
                "link": note.link,
            }
        )

    # return the created notification object
    return note