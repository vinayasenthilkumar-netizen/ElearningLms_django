# import login_required so only logged-in users can access the chat room
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from courses.models import Course, Enrollment
from .models import ChatMessage


# require login to view the chat room
@login_required
# view that shows the chat room for a specific course
def room(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    profile = getattr(request.user, "profile", None)

    role = getattr(profile, "role", None)

    is_teacher = request.user == course.teacher
    # check if the user is enrolled in this course
    is_enrolled = Enrollment.objects.filter(course=course, student=request.user).exists()

    # if the user is not allowed, block access
    if not (is_teacher or is_enrolled):
        # return a forbidden response with a message
        return HttpResponseForbidden("You do not have access to this chat.")

    # get the latest 50 messages (newest first) and include sender info
    chat_messages = course.chat_messages.select_related("sender").order_by("-created_at")[:50]
    # reverse the list so it shows oldest to newest on the page
    chat_messages = list(reversed(chat_messages))

    # render the chat room template with needed data
    return render(request, "chat/room.html", {
        "course": course,
        "chat_messages": chat_messages,
        "is_teacher": is_teacher,
        "is_enrolled": is_enrolled,
    })