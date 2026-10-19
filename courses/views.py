# create your views here.
# (this file holds all the courses app view functions)
# Create your views here.

# import login decorators for protecting views
from django.contrib.auth.decorators import login_required, permission_required
# import helpers for rendering, redirecting, and fetching objects safely
from django.shortcuts import render, redirect, get_object_or_404
# import the built-in user model (used for lookups)
from django.contrib.auth.models import User
# import course app models used by these views
from .models import Course, Enrollment, Material, Folder, Feedback, BlockedStudent, Assignment, Submission
# import notification model (not used directly in active code below)
from accounts.models import Notification
# import channels layer helper (used for websockets)
from channels.layers import get_channel_layer
# import helper to call async code from sync views
from asgiref.sync import async_to_sync
# import shared helper to create notifications (db + websocket)
from accounts.utils import create_notification
# import json response helper for ajax replies
from django.http import JsonResponse,HttpResponseForbidden

# import decorator that forces post requests (not used below)
from django.views.decorators.http import require_POST
# import timezone helpers for date/time comparisons
from django.utils import timezone
# import reverse so we can build urls using route names
from django.urls import reverse
# import the feedback form used for validation
from .forms import FeedbackForm

# import async_to_sync again (duplicate import in your code)
from asgiref.sync import async_to_sync
# import helper to get the active user model
from django.contrib.auth import get_user_model
# import query tools (and exists/outerref again, duplicated)
from django.db.models import Q, Exists, OuterRef,Exists, OuterRef, Prefetch, Avg


# require login to view the course list page
@login_required
# view that shows courses and search and notifications
def course_list(request):
    # try to get the users profile
    profile = getattr(request.user, "profile", None)
    # read the user's role
    role = getattr(profile, "role", None)

    # read the view query param
    view = request.GET.get("view", "enrolled")
    # read the search query text
    search_q = request.GET.get("q", "").strip()
    # read the search scope 
    raw_scope = request.GET.get("scope", "").strip()

    # start with an empty list for user results
    result_users = []
    # start with an empty courses queryset
    courses = Course.objects.none()

    # student logic
  
    if role == "STUDENT":
        # get the active user model
        User = get_user_model()
        # default scope to courses if none provided
        search_scope = raw_scope or "courses"

        # subquery used to mark if the student is enrolled in each course
        enrolled_qs = Enrollment.objects.filter(
            # match the outer course id
            course=OuterRef("pk"),
            # match the current student
            student=request.user
        )

        # student searching users (students or teachers)
        if search_q and search_scope in ["students", "teachers"]:
            # handle student search
            if search_scope == "students":
           
                result_users = (
                  
                    User.objects.filter(profile__role="STUDENT")
                    # filter 
                    .filter(
                        Q(username__icontains=search_q) |
                        Q(first_name__icontains=search_q) |
                        Q(last_name__icontains=search_q) |
                        Q(email__icontains=search_q)
                    )
                    # remove duplicates
                    .distinct()[:12]
                )
            # handle teacher search
            else:  # teachers
             
                result_users = (
                    # only users with teacher role
                    User.objects.filter(profile__role="TEACHER")
                  
                    .filter(
                        Q(username__icontains=search_q) |
                        Q(first_name__icontains=search_q) |
                        Q(last_name__icontains=search_q) |
                        Q(email__icontains=search_q)
                    )
                    # remove duplicates
                    .distinct()[:12]
                )

            # when searching users, don't show course cards
            courses = Course.objects.none()

        # student searching courses
        else:
            # show all courses if view=all
            if view == "all":
              
                courses = (
                    Course.objects.select_related("teacher")
                    .annotate(is_enrolled=Exists(enrolled_qs))
                    .order_by("-created_at")
                )
            # otherwise show only enrolled courses
            else:
                # build queryset for enrolled courses
                courses = (
                    Course.objects.filter(enrollments__student=request.user)
                    .select_related("teacher")
                    .annotate(is_enrolled=Exists(enrolled_qs))
                    .order_by("-created_at")
                )

            # apply course search filters
            if search_q:
                # narrow courses by title description teacher info
                courses = (
                    courses.filter(
                        Q(title__icontains=search_q) |
                        Q(description__icontains=search_q) |
                        Q(teacher__username__icontains=search_q) |
                        Q(teacher__first_name__icontains=search_q) |
                        Q(teacher__last_name__icontains=search_q)
                    )
                    .distinct()
                )

    # teacher logic
   
    elif role == "TEACHER":
        # get the active user model
        User = get_user_model()
      
        search_scope = raw_scope or "my_courses"

    
        base_courses = (
            Course.objects.filter(teacher=request.user)
            .select_related("teacher")
            .order_by("-created_at")
        )

        # start with teacher's own courses
        courses = base_courses

        # only run search logic if query exists
        if search_q:
            # teacher searching students
            if search_scope == "students":
              
                result_users = (
                    User.objects.filter(profile__role="STUDENT")
                    .filter(
                        Q(username__icontains=search_q) |
                        Q(first_name__icontains=search_q) |
                        Q(last_name__icontains=search_q) |
                        Q(email__icontains=search_q)
                    )
                    .distinct()[:12]
                )
                # hide courses when showing user results
                courses = Course.objects.none()

            # teacher searching teachers
            elif search_scope == "teachers":
              
                result_users = (
                    User.objects.filter(profile__role="TEACHER")
                    .filter(
                        Q(username__icontains=search_q) |
                        Q(first_name__icontains=search_q) |
                        Q(last_name__icontains=search_q) |
                        Q(email__icontains=search_q)
                    )
                    .distinct()[:12]
                )
                # hide courses when showing user results
                courses = Course.objects.none()

            # teacher searching own courses
            else: 
              
                courses = (
                    base_courses.filter(
                        Q(title__icontains=search_q) |
                        Q(description__icontains=search_q)
                    )
                    .distinct()
                )

    # fallback when role is missing or not known
    else:
        # default scope value
        search_scope = raw_scope or "courses"
        # show nothing
        courses = Course.objects.none()

    # load notifications for the sidebar
    notifications = request.user.notifications.all()
    # count unread notifications
    unread_count = request.user.notifications.filter(is_read=False).count()

    # render the course list template
    return render(request, "courses/course_list.html", {
        "courses": courses,
        "view": view,
        "notifications": notifications,
        "unread_count": unread_count,
        "search_q": search_q,
        "search_scope": search_scope,
        "result_users": result_users,
    })




@login_required
@permission_required("courses.add_course", raise_exception=True)

def course_create(request):
    # handle submitted form
    if request.method == "POST":
        # read course title
        title = request.POST.get("title", "").strip()
        # read course description
        description = request.POST.get("description", "").strip()

        # block empty title
        if not title:
            return render(
                request,
                "courses/course_create.html",
                {"error": "Title is required."},
            )

        # create the course owned by the current user
        Course.objects.create(
            teacher=request.user,
            title=title,
            description=description,
        )
        # go back to courses list
        return redirect("courses:list")

    # show the create course page on get
    return render(request, "courses/course_create.html")

# require login to edit a course
@login_required
def course_edit(request, course_id):
    # get the course or return 404
    course = get_object_or_404(Course, id=course_id)

    # only the teacher who owns the course can edit it
    if request.user != course.teacher:
        return HttpResponseForbidden("only the course teacher can edit this course.")

    # handle form submission
    if request.method == "POST":
        # get the updated values from the form
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()

        # title should not be empty
        if not title:
            return render(request, "courses/course_edit.html", {
                "course": course,
                "error": "title is required.",
            })

        # update the course fields
        course.title = title
        course.description = description
        course.save()

        # go back to the course detail page after saving
        return redirect("courses:detail", course_id=course.id)

    # show the edit form on get request
    return render(request, "courses/course_edit.html", {
        "course": course,
    })


# require login to delete a course
@login_required
def course_delete(request, course_id):
    # get the course or return 404
    course = get_object_or_404(Course, id=course_id)

    # only the teacher who owns the course can delete it
    if request.user != course.teacher:
        return HttpResponseForbidden("only the course teacher can delete this course.")

    # only delete when the teacher confirms with post
    if request.method == "POST":
        course.delete()
        return redirect("courses:list")

    # show a confirmation page first
    return render(request, "courses/course_delete.html", {
        "course": course,
    })


@login_required
# view that shows one course detail page
def course_detail(request, course_id):
    # load the course or return 404
    course = get_object_or_404(Course, id=course_id)

    # check if the viewer is the course teacher
    is_teacher = (course.teacher == request.user)

    # safely read viewer role from profile
    profile = getattr(request.user, "profile", None)
    # store role value
    viewer_role = getattr(profile, "role", None)
    # check if viewer is a student
    is_student = (viewer_role == "STUDENT")

    # check if the viewer is enrolled
    is_enrolled = Enrollment.objects.filter(course=course, student=request.user).exists()

    # load blocked students for teacher view
    blocked_students = BlockedStudent.objects.filter(course=course).select_related("student")

    # allow materials only to teacher or enrolled students
    can_view_materials = is_teacher or is_enrolled

    # load enrollment list for modal
    enrollments = Enrollment.objects.filter(course=course).select_related("student")
    # load folders and materials only if allowed
    folders = course.folders.prefetch_related("materials") if can_view_materials else []

    # load feedback list newest first
    feedback_list = course.feedback.select_related("student").order_by("-created_at")

    # calculate average rating
    feedback_stats = course.feedback.aggregate(avg_rating=Avg("rating"))
    # pull avg value out of the dict
    avg_rating = feedback_stats["avg_rating"]
    # count feedback items
    feedback_count = feedback_list.count()

    # default my feedback to none
    my_feedback = None
    # default feedback form to none
    feedback_form = None

    # only enrolled students can leave feedback
    if is_student and is_enrolled:
        # find existing feedback if any
        my_feedback = course.feedback.filter(student=request.user).first()

        # prefill form if feedback exists
        if my_feedback:
            feedback_form = FeedbackForm(instance=my_feedback)
        # otherwise show blank form
        else:
            feedback_form = FeedbackForm()

    # render the course detail template
    return render(
        request,
        "courses/course_detail.html",
        {
            "course": course,
            "is_teacher": is_teacher,
            "is_student": is_student,
            "is_enrolled": is_enrolled,
            "can_view_materials": can_view_materials,
            "enrollments": enrollments,
            "folders": folders,
            "feedback_list": feedback_list,
            "avg_rating": avg_rating,
            "feedback_count": feedback_count,
            "my_feedback": my_feedback,
            "feedback_form": feedback_form,
            "blocked_students": blocked_students,
        },
    )


# require login to create folders
@login_required
# view that creates a folder for a course
def create_folder(request, course_id):
    # load the course or return 404
    course = get_object_or_404(Course, id=course_id)

    # only the teacher can create folders
    if request.user != course.teacher:
        return redirect("courses:detail", course_id)

    # handle submitted form
    if request.method == "POST":
        # read folder name
        name = request.POST.get("name")
        # create the folder
        Folder.objects.create(
            name=name,
            course=course
        )
        # go back to course detail
        return redirect("courses:detail", course_id)

    # show folder create page on get
    return render(
        request,
        "courses/folder_create.html",
        {"course": course}
    )



@login_required

def enroll_course(request, course_id):
    # load the course or return 404
    course = get_object_or_404(Course, id=course_id)

    # only allow post requests
    if request.method != "POST":
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"error": "POST required"}, status=400)
        return HttpResponseForbidden("POST required.")

    # safely read role from profile
    profile = getattr(request.user, "profile", None)
    # store role value
    role = getattr(profile, "role", None)

    # only students can enroll
    if role != "STUDENT":
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"error": "Only students can enroll."}, status=403)
        return HttpResponseForbidden("Only students can enroll.")

    # block enrollment if student is blocked
    blocked = BlockedStudent.objects.filter(course=course, student=request.user).exists()
    if blocked:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"error": "You are blocked from this course."}, status=403)
        return HttpResponseForbidden("You are blocked from this course.")

    # create enrollment if it does not exist
    enrollment, created = Enrollment.objects.get_or_create(course=course, student=request.user)

    # notify teacher only when enrollment is new
    if created:
        create_notification(
            user=course.teacher,
            title="New course enrollment",
            message=f"{request.user.username} enrolled in {course.title}.",
            course=course,
            link=reverse("courses:detail", args=[course.id]),
        )

    # count current enrollments
    count = Enrollment.objects.filter(course=course).count()

    # return json if this was an ajax request
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "created": created,
            "count": count,
        })

    # otherwise redirect back to course detail
    return redirect("courses:detail", course_id=course.id)


@login_required

def material_add(request, course_id):
    # load the course or return 404
    course = get_object_or_404(Course, id=course_id)

    # only the course teacher can add materials
    if not request.user.has_perm("courses.add_course") or course.teacher != request.user:
        return HttpResponseForbidden("Only the course teacher can add materials.")

    # load folders for dropdown
    folders = Folder.objects.filter(course=course)

    # handle submitted form
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
    
        file = request.FILES.get("file")

        folder_id = request.POST.get("folder_id")

        # validate required fields
        if not title or not file or not folder_id:
            return render(request, "courses/material_add.html", {
                "course": course,
                "folders": folders,
                "error": "Title, folder and file are required."
            })

        # load the folder and ensure it belongs to this course
        folder = get_object_or_404(Folder, id=folder_id, course=course)

        # create the material record
        material = Material.objects.create(
            course=course,
            folder=folder,
            title=title,
            file=file
        )

        # notify all enrolled students about new material
        for enrollment in Enrollment.objects.filter(course=course).select_related("student"):
            create_notification(
                user=enrollment.student,
                title="New material uploaded",
                message=f"New material was added in {course.title}: {material.title}",
                course=course,
                link=reverse("courses:detail", args=[course.id]),
            )

        # go back to course detail after upload
        return redirect("courses:detail", course_id=course.id)

    # show upload page on get
    return render(request, "courses/material_add.html", {
        "course": course,
        "folders": folders
    })


# require login to remove a student
@login_required
# ajax view that removes a student from a course
def remove_student(request, course_id, student_id):
    # only allow post requests
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    # load the course or return 404
    course = get_object_or_404(Course, id=course_id)

    # only the teacher can remove students
    if request.user != course.teacher:
        return JsonResponse({"error": "Not allowed"}, status=403)

    # load the student user or return 404
    student = get_object_or_404(User, id=student_id)

    # delete the enrollment record
    Enrollment.objects.filter(
        course=course,
        student=student
    ).delete()

    # notify the student that they were removed
    create_notification(
        user=student,
        title="Removed from course",
        message=f"You were removed from {course.title}.",
        course=course,
        link=reverse("courses:list"),
    )

    # count remaining enrollments
    count = Enrollment.objects.filter(course=course).count()

    # return json success response
    return JsonResponse({
        "success": True,
        "student_id": student_id,
        "count": count,
    })


# require login to block a student
@login_required
# ajax view that blocks a student from a course
def block_student(request, course_id, student_id):
    # only allow post requests
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    # load the course or return 404
    course = get_object_or_404(Course, id=course_id)

    # only the teacher can block students
    if request.user != course.teacher:
        return JsonResponse({"error": "Not allowed"}, status=403)

    # load the student user or return 404
    student = get_object_or_404(User, id=student_id)

    # create a blocked record if it does not exist
    BlockedStudent.objects.get_or_create(
        teacher=request.user,
        student=student,
        course=course
    )

    # remove enrollment if they were enrolled
    Enrollment.objects.filter(
        course=course,
        student=student
    ).delete()

    # notify the student that they were blocked
    create_notification(
        user=student,
        title="Blocked from course",
        message=f"You were blocked from {course.title}.",
        course=course,
        link=reverse("courses:list"),
    )

    # count remaining enrollments
    count = Enrollment.objects.filter(course=course).count()

    # return json success response
    return JsonResponse({
        "success": True,
        "student_id": student_id,
        "count": count,
    })


@login_required
# ajax view that lets the teacher unblock a student from a course
def unblock_student(request, course_id, student_id):
    # only allow post requests
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    # load the course or return 404
    course = get_object_or_404(Course, id=course_id)

    # only the teacher who owns the course can unblock students
    if request.user != course.teacher:
        return JsonResponse({"error": "Not allowed"}, status=403)

    # load the student user or return 404
    student = get_object_or_404(User, id=student_id)

    # delete the blocked record if it exists
    deleted_count, _ = BlockedStudent.objects.filter(
        teacher=request.user,
        student=student,
        course=course
    ).delete()

    # if nothing was deleted, the student was not blocked
    if deleted_count == 0:
        return JsonResponse({"error": "Student was not blocked."}, status=404)

    # notify the student that they were unblocked
    create_notification(
        user=student,
        title="Unblocked from course",
        message=f"You were unblocked from {course.title}.",
        course=course,
        link=reverse("courses:list"),
    )

    # count how many blocked students are left for this course
    blocked_count = BlockedStudent.objects.filter(course=course).count()

    # return success response for ajax
    return JsonResponse({
        "success": True,
        "student_id": student_id,
        "blocked_count": blocked_count,
    })

# require login to delete a material
@login_required

def material_delete(request, course_id, material_id):
    # load the material or return 404
    material = get_object_or_404(Material, id=material_id, course_id=course_id)

    # only the course teacher can delete materials
    if request.user != material.course.teacher:
        return HttpResponseForbidden()

    # delete only on post request
    if request.method == "POST":
        material.delete()
        return redirect("courses:detail", course_id)

    # show confirmation page on get
    return render(request, "courses/material_delete.html", {
        "material": material,
        "course": material.course,
    })



@login_required

def folder_delete(request, course_id, folder_id):
    # only allow post requests
    if request.method != "POST":
        return HttpResponseForbidden("POST required.")

    # load the course or return 404
    course = get_object_or_404(Course, id=course_id)

    # only the teacher can delete folders
    if request.user != course.teacher:
        return HttpResponseForbidden("Only the teacher can delete folders.")

    # load the folder or return 404
    folder = get_object_or_404(Folder, id=folder_id, course=course)

    # delete materials in this folder first
    Material.objects.filter(folder=folder).delete()
    # delete the folder itself
    folder.delete()

    # go back to course detail
    return redirect("courses:detail", course_id=course.id)


# import json response again (duplicate import in your code)
from django.http import JsonResponse


@login_required
# ajax view that creates updates feedback for a course
def feedback_submit(request, course_id):
    # load the course or return 404
    course = get_object_or_404(Course, id=course_id)

    # only allow post requests
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    # safely read role from profile
    profile = getattr(request.user, "profile", None)
    # store role value
    role = getattr(profile, "role", None)

    # only students can leave feedback
    if role != "STUDENT":
        return JsonResponse({"error": "Only students can leave feedback."}, status=403)

    # student must be enrolled to leave feedback
    is_enrolled = Enrollment.objects.filter(course=course, student=request.user).exists()
    if not is_enrolled:
        return JsonResponse({"error": "You must be enrolled to leave feedback."}, status=403)

    # validate incoming form data
    form = FeedbackForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"error": "Invalid form"}, status=400)

    # create or update feedback for this student and course
    feedback, created = Feedback.objects.update_or_create(
        course=course,
        student=request.user,
        defaults={
            "rating": form.cleaned_data["rating"],
            "comment": form.cleaned_data["comment"],
        },
    )

    # notify the teacher about new/updated feedback
    create_notification(
        user=course.teacher,
        title="New feedback received" if created else "Feedback updated",
        message=f"{request.user.username} {'left' if created else 'updated'} feedback for {course.title}.",
        course=course,
        link=reverse("courses:detail", args=[course.id]),
    )

    # recompute the course average rating
    avg = course.feedback.aggregate(avg_rating=Avg("rating"))["avg_rating"]

    # return json response including updated average
    return JsonResponse({
        "success": True,
        "rating": feedback.rating,
        "comment": feedback.comment,
        "avg_rating": round(avg, 1) if avg else 0,
    })



@login_required
# view that shows assignment submissions for a course
def submissions_page(request, course_id):
    # load the course or return 404
    course = get_object_or_404(Course, id=course_id)

    # safely read role from profile
    profile = getattr(request.user, "profile", None)
    # store role value
    role = getattr(profile, "role", None)

    # check if viewer is teacher
    is_teacher = request.user == course.teacher
    is_student = role == "STUDENT"
  
    is_enrolled = Enrollment.objects.filter(course=course, student=request.user).exists()

    # block access if not teacher or enrolled student
    if not (is_teacher or is_enrolled):
        return HttpResponseForbidden("You do not have access to submissions for this course.")

    # load assignments and prefetch submissions with students
    assignments = list(course.assignments.prefetch_related("submissions__student"))

    # attach the student's own submission for each assignment
    if is_student:
        # build a quick map of assignment_id -> submission
        my_map = {
            s.assignment_id: s
            for s in Submission.objects.filter(
                assignment__course=course,
                student=request.user
            ).select_related("assignment")
        }

        # attach my_submission for each assignment
        for a in assignments:
            a.my_submission = my_map.get(a.id)

    # teacher does not need my_submission
    else:
        for a in assignments:
            a.my_submission = None

    # render the submissions page template
    return render(request, "courses/submissions_page.html", {
        "course": course,
        "is_teacher": is_teacher,
        "is_student": is_student,
        "is_enrolled": is_enrolled,
        "assignments": assignments,
        "now": timezone.now(),
    })


# require login to create assignments
@login_required
# view that creates a new assignment (teacher only)
def assignment_create(request, course_id):
    # load the course or return 404
    course = get_object_or_404(Course, id=course_id)

    # only the teacher can create assignments
    if request.user != course.teacher:
        return HttpResponseForbidden("Only the course teacher can create assignments.")

    # handle submitted form
    if request.method == "POST":
     
        title = request.POST.get("title", "").strip()
    
        instructions = request.POST.get("instructions", "").strip()
   
        due_date = request.POST.get("due_date", "").strip()

        # block empty title
        if not title:
            return render(request, "courses/assignment_create.html", {
                "course": course,
                "error": "Title is required.",
            })

        assignment = Assignment(
            course=course,
            title=title,
            instructions=instructions,
        )


        if due_date:
            from django.utils.dateparse import parse_datetime
            parsed = parse_datetime(due_date)
            if parsed:
                assignment.due_date = parsed

        # save the assignment
        assignment.save()

        # notify enrolled students about the new assignment
        for enrollment in Enrollment.objects.filter(course=course).select_related("student"):
            create_notification(
                user=enrollment.student,
                title="New assignment created",
                message=f"A new assignment was added in {course.title}: {assignment.title}",
                course=course,
                link=reverse("courses:submissions_page", args=[course.id]),
            )

        # go back to submissions page after creating
        return redirect("courses:submissions_page", course_id=course.id)

    # show create assignment page on get
    return render(request, "courses/assignment_create.html", {"course": course})


@login_required
# view that lets a student submit or update their work for an assignment
def submission_upload(request, course_id, assignment_id):
    # load the course or return 404
    course = get_object_or_404(Course, id=course_id)
    # load the assignment 
    assignment = get_object_or_404(Assignment, id=assignment_id, course=course)
    # deadline check
    if assignment.due_date and timezone.now() > assignment.due_date:
        return HttpResponseForbidden("Deadline has passed. Submissions are locked.")

    # safely get the user's profile
    profile = getattr(request.user, "profile", None)
    # read the role from the profile
    role = getattr(profile, "role", None)

    # only students are allowed to submit work
    if role != "STUDENT":
        return HttpResponseForbidden("Only students can submit work.")

    # check that the student is enrolled in this course
    is_enrolled = Enrollment.objects.filter(course=course, student=request.user).exists()
    if not is_enrolled:
        return HttpResponseForbidden("You must be enrolled in this course.")

    # check if the student already has a submission for this assignment
    existing_submission = Submission.objects.filter(
        assignment=assignment,
        student=request.user
    ).first()

    # handle the form submit
    if request.method == "POST":
        # read the uploaded file
        file = request.FILES.get("file")
        # read the optional note text
        note = request.POST.get("note", "").strip()

        # if this is a first submission, file is required
        if not file and not existing_submission:
            return render(request, "courses/submission_upload.html", {
                "course": course,
                "assignment": assignment,
                "submission": existing_submission,
                "error": "Please choose a file.",
            })

        # track whether this is an update or a new submission
        was_update = existing_submission is not None

        # update existing submission if it exists
        if existing_submission:
            # replace file only if a new file was uploaded
            if file:
                existing_submission.file = file
            # update the note
            existing_submission.note = note
            # save changes
            existing_submission.save()
            # use the updated object as the submission
            submission = existing_submission
        # otherwise create a brand new submission
        else:
            submission = Submission.objects.create(
                assignment=assignment,
                student=request.user,
                file=file,
                note=note,
            )

        # notify the teacher that a submission was made or updated
        # Notify teacher
        create_notification(
            user=course.teacher,
            title="Student submission received" if not was_update else "Student submission updated",
            message=f"{request.user.username} {'updated' if was_update else 'submitted'} work for {assignment.title}.",
            course=course,
            link=reverse("courses:submissions_page", args=[course.id]),
        )

        # go back to the submissions page after saving
        return redirect("courses:submissions_page", course_id=course.id)

    # show the upload page on get request
    return render(request, "courses/submission_upload.html", {
        "course": course,
        "assignment": assignment,
        "submission": existing_submission,
    })


# require login to grade a submission
@login_required
# ajax view that lets the teacher grade a student's submission
def submission_grade(request, course_id, submission_id):
    # load the course or return 404
    course = get_object_or_404(Course, id=course_id)

    # only the course teacher can grade submissions
    if request.user != course.teacher:
        return JsonResponse({"error": "Not allowed"}, status=403)

    # only allow post requests
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    # load the submission and make sure it belongs to this course
    submission = get_object_or_404(
        Submission,
        id=submission_id,
        assignment__course=course
    )

    # read the grade input
    grade = request.POST.get("grade", "").strip()
    # read the teacher comment input
    teacher_comment = request.POST.get("teacher_comment", "").strip()

    # save the grade on the submission
    submission.grade = grade
    # save the teacher comment on the submission
    submission.teacher_comment = teacher_comment
    # save changes
    submission.save()

    # notify the student that their submission was graded
    # Notify student
    create_notification(
        user=submission.student,
        title="Submission graded",
        message=f"Your submission for {submission.assignment.title} has been graded.",
        course=course,
        link=reverse("courses:submissions_page", args=[course.id]),
    )

    # return json success response
    return JsonResponse({
        "success": True,
        "submission_id": submission.id,
        "grade": submission.grade,
        "teacher_comment": submission.teacher_comment,
    })


# require login to edit an assignment
@login_required
# view that lets the teacher edit an assignment
def assignment_edit(request, course_id, assignment_id):
    # load the course or return 404
    course = get_object_or_404(Course, id=course_id)
    # load the assignment and make sure it belongs to this course
    assignment = get_object_or_404(Assignment, id=assignment_id, course=course)

    # only the course teacher can edit assignments
    if request.user != course.teacher:
        return HttpResponseForbidden("Only the course teacher can edit assignments.")

    # handle the form submit
    if request.method == "POST":
        old_due_date = assignment.due_date
        old_title = assignment.title
        old_instructions = assignment.instructions
        # read the updated title
        title = request.POST.get("title", "").strip()
        # read the updated instructions
        instructions = request.POST.get("instructions", "").strip()
        # read the updated due date string (optional)
        due_date = request.POST.get("due_date", "").strip()

        # block empty title
        if not title:
            return render(request, "courses/assignment_edit.html", {
                "course": course,
                "assignment": assignment,
                "error": "Title is required.",
            })
        
        # save updated title
        assignment.title = title
        # save updated instructions
        assignment.instructions = instructions

        # import datetime parser to handle datetime-local input
        from django.utils.dateparse import parse_datetime
        # if due date was provided, try to parse it
        if due_date:
            parsed = parse_datetime(due_date)
            assignment.due_date = parsed if parsed else None
        # if due date is empty, clear it
        else:
            assignment.due_date = None

        due_date_changed = assignment.due_date != old_due_date
        content_changed = (
            assignment.title != old_title or
            assignment.instructions != old_instructions
        )
        # save assignment changes
        assignment.save()

        # notify enrolled students if assignment changed
        enrollments = Enrollment.objects.filter(course=course).select_related("student")

        # if the deadline changed, remove old reminder notifications first
        if due_date_changed:
            Notification.objects.filter(
                course=course,
                title__in=[
                    "Assignment due in 24 hours",
                    "Assignment due in 2 hours",
                    "Course assignment due in 24 hours",
                    "Course assignment due in 2 hours",
                ],
                message__icontains=assignment.title,
            ).delete()

        # send notifications to students
        for enrollment in enrollments:
            student = enrollment.student

            # deadline changed notification
            if due_date_changed:
                create_notification(
                    user=student,
                    title="Assignment deadline changed",
                    message=f"The deadline for {assignment.title} in {course.title} was updated.",
                    course=course,
                    link=reverse("courses:submissions_page", args=[course.id]),
                )

            # general update notification
            elif content_changed:
                create_notification(
                    user=student,
                    title="Assignment updated",
                    message=f"The assignment {assignment.title} in {course.title} was updated.",
                    course=course,
                    link=reverse("courses:submissions_page", args=[course.id]),
                )


        # go back to submissions page after saving
        return redirect("courses:submissions_page", course_id=course.id)

    # show the edit page on get request
    return render(request, "courses/assignment_edit.html", {
        "course": course,
        "assignment": assignment,
    })


@login_required
# view that lets the teacher delete an assignment
def assignment_delete(request, course_id, assignment_id):
    # load the course or return 404
    course = get_object_or_404(Course, id=course_id)
    # load the assignment 
    assignment = get_object_or_404(Assignment, id=assignment_id, course=course)

    # only the course teacher can delete assignments
    if request.user != course.teacher:
        return HttpResponseForbidden("Only the course teacher can delete assignments.")

   
    if request.method == "POST":
        # list of reminder titles that might exist for this assignment
        reminder_titles = [
            "Assignment due in 24 hours",
            "Assignment due in 2 hours",
            "Course assignment due in 24 hours",
            "Course assignment due in 2 hours",
        ]

        # delete reminder notifications 
        Notification.objects.filter(
            course=course,
            title__in=reminder_titles,
            message__icontains=assignment.title,
        ).delete()

        # delete the assignment itself
        assignment.delete()
        # go back to submissions page after deletion
        return redirect("courses:submissions_page", course_id=course.id)

    # show the delete confirmation page 
    return render(request, "courses/assignment_delete.html", {
        "course": course,
        "assignment": assignment,
    })


# require login to view the whiteboard page
@login_required
# view that shows the live whiteboard page for a course
def whiteboard_page(request, course_id):
    # load the course or return 404
    course = get_object_or_404(Course, id=course_id)

    # check if the viewer is the course teacher
    is_teacher = request.user == course.teacher
    # check if the viewer is enrolled in the course
    is_enrolled = Enrollment.objects.filter(course=course, student=request.user).exists()

    # block access if not teacher or enrolled student
    if not (is_teacher or is_enrolled):
        return HttpResponseForbidden("You do not have access to this whiteboard.")

    # render the whiteboard template
    return render(request, "courses/whiteboard.html", {
        "course": course,
        "is_teacher": is_teacher,
        "is_enrolled": is_enrolled,
    })