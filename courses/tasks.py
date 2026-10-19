from datetime import timedelta
from accounts.utils import create_notification
from celery import shared_task
from django.utils import timezone
from django.urls import reverse

from accounts.models import Notification
from .models import Assignment, Enrollment


# celery task that sends reminders before assignment deadlines
@shared_task
def send_deadline_reminders():
    now = timezone.now()
    in_24_hours = now + timedelta(hours=24)
    in_2_hours = now + timedelta(hours=2)

    reminder_titles = [
        "Assignment due in 24 hours",
        "Assignment due in 2 hours",
        "Course assignment due in 24 hours",
        "Course assignment due in 2 hours",
    ]

    # clean up reminder notifications for assignments that are already past due
    expired_assignments = Assignment.objects.filter(
        due_date__isnull=False,
        due_date__lte=now,
    ).select_related("course")

    for expired in expired_assignments:
        tag = f"[A{expired.id}]"
        Notification.objects.filter(
            course=expired.course,
            title__in=[
                "Assignment due in 24 hours",
                "Assignment due in 2 hours",
                "Course assignment due in 24 hours",
                "Course assignment due in 2 hours",
            ],
            message__contains=tag,
        ).delete()

    assignments = Assignment.objects.filter(
        due_date__isnull=False,
        due_date__gt=now,
        due_date__lte=in_24_hours,
    ).select_related("course", "course__teacher")

    count = 0

    for assignment in assignments:
        tag = f"[A{assignment.id}]"
        submission_link = reverse("courses:submissions_page", args=[assignment.course.id])
        due_display = timezone.localtime(assignment.due_date).strftime("%b %d, %Y %H:%M")

        enrollments = Enrollment.objects.filter(course=assignment.course).select_related("student")

        # -------------------------------
        # 2-hour reminder
        # -------------------------------
        if assignment.due_date <= in_2_hours:
            teacher_already_sent = Notification.objects.filter(
                user=assignment.course.teacher,
                title="Course assignment due in 2 hours",
                message__contains=tag,
            ).exists()

            if not teacher_already_sent:
                create_notification(
                    user=assignment.course.teacher,
                    title="Course assignment due in 2 hours",
                    message=f"{tag} {assignment.title} in {assignment.course.title} closes within 2 hours. Due: {due_display}",
                    course=assignment.course,
                    link=submission_link,
                )
                count += 1

            for enrollment in enrollments:
                student_already_sent = Notification.objects.filter(
                    user=enrollment.student,
                    title="Assignment due in 2 hours",
                    message__contains=tag,
                ).exists()

                if not student_already_sent:
                    create_notification(
                        user=enrollment.student,
                        title="Assignment due in 2 hours",
                        message=f"{tag} {assignment.title} in {assignment.course.title} is due within 2 hours. Due: {due_display}",
                        course=assignment.course,
                        link=submission_link,
                    )
                    count += 1

        # -------------------------------
        # 24-hour reminder
        # -------------------------------
        else:
            teacher_already_sent = Notification.objects.filter(
                user=assignment.course.teacher,
                title="Course assignment due in 24 hours",
                message__contains=tag,
            ).exists()

            if not teacher_already_sent:
                create_notification(
                    user=assignment.course.teacher,
                    title="Course assignment due in 24 hours",
                    message=f"{tag} {assignment.title} in {assignment.course.title} closes within 24 hours. Due: {due_display}",
                    course=assignment.course,
                    link=submission_link,
                )
                count += 1

            for enrollment in enrollments:
                student_already_sent = Notification.objects.filter(
                    user=enrollment.student,
                    title="Assignment due in 24 hours",
                    message__contains=tag,
                ).exists()

                if not student_already_sent:
                    create_notification(
                        user=enrollment.student,
                        title="Assignment due in 24 hours",
                        message=f"{tag} {assignment.title} in {assignment.course.title} is due within 24 hours. Due: {due_display}",
                        course=assignment.course,
                        link=submission_link,
                    )
                    count += 1

    return f"Created {count} deadline reminder notification(s)."


# celery task that notifies users when an assignment just closed
@shared_task
def send_assignment_closed_notifications():
    now = timezone.now()

    # find assignments that are already closed
    closed_assignments = Assignment.objects.filter(
        due_date__isnull=False,
        due_date__lte=now,
        closed_notification_sent=False,
    ).select_related("course", "course__teacher")

    count = 0

    for a in closed_assignments:
        tag = f"[A{a.id}]"
        due_display = timezone.localtime(a.due_date).strftime("%b %d, %Y %H:%M")
        link = reverse("courses:submissions_page", args=[a.course.id])

        # teacher notification
        create_notification(
            user=a.course.teacher,
            title="Assignment closed",
            message=f"{tag} {a.title} in {a.course.title} is now closed. Due was: {due_display}",
            course=a.course,
            link=link,
        )
        count += 1

        # student notifications
        for e in Enrollment.objects.filter(course=a.course).select_related("student"):
            create_notification(
                user=e.student,
                title="Assignment closed",
                message=f"{tag} {a.title} in {a.course.title} is now closed. Due was: {due_display}",
                course=a.course,
                link=link,
            )
            count += 1

        # mark this assignment as already handled
        a.closed_notification_sent = True
        a.save(update_fields=["closed_notification_sent"])

    return f"Created {count} assignment-closed notification(s)."