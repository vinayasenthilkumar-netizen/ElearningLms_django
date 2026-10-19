
from django.conf import settings
from django.db import models


# model that stores chat messages for a course
class ChatMessage(models.Model):
    # link each chat message to a course
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="chat_messages",
    )
    # link each chat message to the user who sent it
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_chat_messages",
    )
    # store the message text
    message = models.TextField()
    # store the time the message was created
    created_at = models.DateTimeField(auto_now_add=True)

    # extra settings for this model
    class Meta:
        # sort messages from oldest to newest
        ordering = ["created_at"]

    # show a readable name for this message in admin and logs
    def __str__(self):
        # return course title and sender username
        return f"{self.course.title} - {self.sender.username}"