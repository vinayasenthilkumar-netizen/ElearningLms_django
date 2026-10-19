from django.db.models.signals import post_delete
from django.dispatch import receiver

from accounts.models import Notification
from .models import Assignment

@receiver(post_delete, sender=Assignment)
def delete_assignment_reminder_notifications(sender, instance, **kwargs):
    tag = f"[A{instance.id}]"

    Notification.objects.filter(
        course=instance.course,
        title__in=[
            "Assignment due in 24 hours",
            "Assignment due in 2 hours",
            "Course assignment due in 24 hours",
            "Course assignment due in 2 hours",
            "Assignment closed",
        ],
        message__contains=tag,
    ).delete()