
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.contrib.auth import get_user_model
from django.utils import timezone
from courses.models import Enrollment, Assignment,Course
from .models import Profile, Notification, StatusUpdate, TodoItem
from .forms import SignupForm, ProfileForm, StatusUpdateForm, TodoForm

# apply never_cache to all requests handled by this class-based view
@method_decorator(never_cache, name="dispatch")

class CustomLoginView(LoginView):

    template_name = "registration/login.html"


# apply never_cache to all requests handled by this class-based view
@method_decorator(never_cache, name="dispatch")

class CustomLogoutView(LogoutView):

    pass

# view that handles user signup
def signup(request):
    # check if the form was submitted
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            # create the user object but don’t save yet
            user = form.save(commit=False)
            user.first_name = form.cleaned_data.get("first_name", "")
            user.last_name = form.cleaned_data.get("last_name", "")
            user.email = form.cleaned_data.get("email", "")
            user.save()

            role = form.cleaned_data["role"]
            students_group, _ = Group.objects.get_or_create(name="Students")
            teachers_group, _ = Group.objects.get_or_create(name="Teachers")

            # if the user chose teacher, assign teacher group
            if role == "TEACHER":
                # add user to the teachers group
                user.groups.add(teachers_group)
            # otherwise assign student group
            else:
                # add user to the students group
                user.groups.add(students_group)

            # create or update the profile with the selected role
            Profile.objects.update_or_create(user=user, defaults={"role": role})

            # log the user in right after signup
            login(request, user)
            # send the user to the course list page
            return redirect("courses:list")
    else:
   
        form = SignupForm()

    # render the signup page with the form
    return render(request, "accounts/signup.html", {"form": form})


@login_required

def dashboard(request):
    profile = getattr(request.user, "profile", None)
    # read the role from the profile if it exists
    role = getattr(profile, "role", None)
    notifications = request.user.notifications.all()[:10]
    # count how many notifications are unread
    unread_count = request.user.notifications.filter(is_read=False).count()

    # start with empty lists for courses
    enrolled_courses = []
    # start with empty lists for courses taught
    teaching_courses = []

    # if the user is a student, load enrolled courses
    if role == "STUDENT":
        # build the enrollment query with related course and teacher data
        enrolled_courses = (
            # find enrollments where this user is the student
            Enrollment.objects.filter(student=request.user)
            # pull related course and teacher in the same query
            .select_related("course", "course__teacher")
        )
    # if the user is a teacher, load courses they teach
    elif role == "TEACHER":
        # get courses taught by the teacher
        teaching_courses = request.user.courses_taught.all()

    # render the dashboard template with all needed data
    return render(request, "accounts/dashboard.html", {
        # pass the user's role
        "role": role,
        "notifications": notifications,
        "unread_count": unread_count,
        "enrolled_courses": enrolled_courses,
        "teaching_courses": teaching_courses,
    })

# require login to mark a notification as read
@login_required
# view to mark a notification as read
def notification_read(request, notification_id):
    # find the notification that belongs to this user or return 404
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )

    # only allow post requests for this action
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)
    
    # block editing reminder notifications
    if "due in" in notification.title.lower():
        return JsonResponse({"error": "Reminder notifications cannot be modified."}, status=403)

    # mark the notification as read
    notification.is_read = True
    # save the change to the database
    notification.save()

    # recalculate unread notifications count
    unread_count = request.user.notifications.filter(is_read=False).count()

    # return a json success response
    return JsonResponse({
        "success": True,

        "notification_id": notification.id,
      
        "unread_count": unread_count,
    })

@login_required
# view for teachers to search users and courses
def teacher_search(request):
    # try to get the user's profile
    profile = getattr(request.user, "profile", None)
    # read the role from the profile
    role = getattr(profile, "role", None)

    # block access if the user is not a teacher
    if role != "TEACHER":
        # return forbidden response with a message
        return HttpResponseForbidden("Only teachers can use search.")

    # get the user model
    User = get_user_model()
    # read the search query from the url
    q = request.GET.get("q", "").strip()


    students = User.objects.none()
    teachers = User.objects.none()
    my_courses = Course.objects.none()
    module_matches = Course.objects.none()

    # only run search if query is not empty
    if q:
        # build a user search filter across multiple fields
        user_query = (
            # match username
            Q(username__icontains=q) |
            # match first name
            Q(first_name__icontains=q) |
            # match last name
            Q(last_name__icontains=q) |
            # match email
            Q(email__icontains=q)
        )

        # find students matching the query
        students = (
            # filter only student profiles
            User.objects.filter(profile__role="STUDENT")
            # apply the name/email query
            .filter(user_query)
            # avoid duplicates
            .distinct()[:10]
        )

        # find teachers matching the query
        teachers = (
            # filter only teacher profiles
            User.objects.filter(profile__role="TEACHER")
            # apply the name/email query
            .filter(user_query)
            # avoid duplicates
            .distinct()[:10]
        )

        # find courses taught by the current teacher that match the query
        my_courses = (
            # only courses taught by this teacher
            Course.objects.filter(teacher=request.user)
            # match on title or description
            .filter(
                # match title
                Q(title__icontains=q) |
                # match description
                Q(description__icontains=q)
            )
            # avoid duplicates
            .distinct()[:10]
        )

        # find any courses that match the query
        module_matches = (
            # search across all courses
            Course.objects.filter(
                # match title
                Q(title__icontains=q) |
                # match description
                Q(description__icontains=q)
            )
            # avoid duplicates
            .distinct()[:10]
        )

    # render the search page with results
    return render(request, "accounts/search.html", {
        # send the query back to the template
        "q": q,
        "students": students,
        "teachers": teachers,
        "my_courses": my_courses,
        "module_matches": module_matches,
    })


@login_required
# dashboard view that redirects to the user's own profile page
def dashboard(request):

    return profile_home(request, username=request.user.username)


@login_required
# view that shows a user's profile home page
def profile_home(request, username):
    # get the active user model
    User = get_user_model()
    # find the target user by username or return 404
    target_user = get_object_or_404(User, username=username)

    # get or create the profile for the target user
    target_profile, _ = Profile.objects.get_or_create(
        user=target_user,
        defaults={"role": Profile.Role.STUDENT},
    )

    # check if the viewer is viewing their own profile
    viewer_is_owner = request.user == target_user
    # store the target user's role
    target_role = target_profile.role

    # load up to 20 status updates from the target user
    status_updates = target_user.status_updates.all()[:20]

    # start with empty lists for course sections
    teaching_courses = []
    enrolled_courses = []
    upcoming_deadlines = []

    # if the target user is a teacher, show teaching courses and deadlines
    if target_role == "TEACHER":
        # load courses taught by the target teacher
        teaching_courses = target_user.courses_taught.all().order_by("-created_at")
        # load upcoming assignment deadlines for the teacher's courses
        upcoming_deadlines = (
            Assignment.objects.filter(
                course__teacher=target_user,
                due_date__isnull=False,
                due_date__gte=timezone.now()
            )
            .select_related("course")
            .order_by("due_date")[:5]
        )
    # otherwise treat the target user as a student
    else:
        # load courses the target student is enrolled in
        enrolled_courses = (
            Enrollment.objects.filter(student=target_user)
            .select_related("course", "course__teacher")
            .order_by("-enrolled_at")
        )
        # load upcoming assignment deadlines for the student's enrolled courses
        upcoming_deadlines = (
            Assignment.objects.filter(
                course__enrollments__student=target_user,
                due_date__isnull=False,
                due_date__gte=timezone.now(),
            )
            .select_related("course")
            .distinct()
            .order_by("due_date")[:5]
        )

    # only show notifications and unread count if the viewer owns the profile

    notifications = request.user.notifications.all()[:6] if viewer_is_owner else []
    unread_count = request.user.notifications.filter(is_read=False).count() if viewer_is_owner else 0

    # default forms to none
    status_form = None
    todo_form = None
    # start with an empty todo queryset
    todos = TodoItem.objects.none()

    # only show to-do list if the viewer is the owner

    if viewer_is_owner:
 
        todos = request.user.todos.all()
   
        todo_form = TodoForm()

    # allow status updates only for the profile owner who is a student

    if viewer_is_owner and target_role == "STUDENT":
        # create a blank status update form
        status_form = StatusUpdateForm()

    # render the profile page

    return render(request, "accounts/profile_home.html", {
        "target_user": target_user,
        "target_profile": target_profile,
        "viewer_is_owner": viewer_is_owner,
        "target_role": target_role,
        "status_updates": status_updates,
        "status_form": status_form,
        "teaching_courses": teaching_courses,
        "enrolled_courses": enrolled_courses,
        "upcoming_deadlines": upcoming_deadlines if viewer_is_owner else [],
        "notifications": notifications,
        "unread_count": unread_count,
        "todo_form": todo_form,
        "todos": todos if viewer_is_owner else [],
    })

# require login to create a todo item
@login_required
# view to create a new todo
def todo_create(request):
    # only handle creation on post
    if request.method == "POST":
        
        form = TodoForm(request.POST)
       
        if form.is_valid():
         
            todo = form.save(commit=False)
       
            todo.user = request.user
        
            todo.save()
    # always go back to the dashboard after this
    return redirect("dashboard")


@login_required
# view to edit an existing todo
def todo_edit(request, todo_id):
    # fetch the todo that belongs to this user or return 404
    todo = get_object_or_404(TodoItem, id=todo_id, user=request.user)

    if request.method == "POST":
        # bind posted data to the form using the existing todo
        form = TodoForm(request.POST, instance=todo)
     
        if form.is_valid():
      
            form.save()
          
            return redirect("dashboard")
    # if not submitted, show the form with existing data
    else:
        # create the form pre filled with the todo data
        form = TodoForm(instance=todo)

    # render the edit page with the form and todo
    return render(request, "accounts/todo_edit.html", {
        # pass the form
        "form": form,
        # pass the todo item
        "todo": todo,
    })


# require login to delete a todo item
@login_required
# view to delete a todo item
def todo_delete(request, todo_id):
    # fetch the todo that belongs to this user or return 404
    todo = get_object_or_404(TodoItem, id=todo_id, user=request.user)

    # only delete on post
    if request.method == "POST":
        # delete the todo item
        todo.delete()

    # go back to dashboard after delete attempt
    return redirect("dashboard")

# require login to edit a profile
@login_required
# view to edit the logged-in user's profile
def profile_edit(request):
    # get or create the profile for the logged in user
    profile, _ = Profile.objects.get_or_create(
        # link to the current user
        user=request.user,
        # default role to student if profile is new
        defaults={"role": Profile.Role.STUDENT},
    )

    # if the form is submitted, save changes
    if request.method == "POST":
        # create the form with posted data and files
        form = ProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        # validate the form
        if form.is_valid():
            # save the profile fields
            profile = form.save()


            request.user.first_name = form.cleaned_data["first_name"]
       
            request.user.last_name = form.cleaned_data["last_name"]
      
            request.user.email = form.cleaned_data["email"]
            # save user changes
            request.user.save()

            # go back to dashboard after saving
            return redirect("dashboard")
    # if it’s not a post request, show the form
    else:
        # create the form pre-filled with existing profile data
        form = ProfileForm(instance=profile, user=request.user)

    # render the profile edit page with the form
    return render(request, "accounts/profile_edit.html", {
        # pass the form to the template
        "form": form,
    })


# require login to create a status update
@login_required
# view to create a new status update (students only)
def status_create(request):
    # try to get the user's profile
    profile = getattr(request.user, "profile", None)

    role = getattr(profile, "role", None)

    # block teachers from posting statuses
    if role != "STUDENT":
    
        return HttpResponseForbidden("Only students can post status updates.")


    if request.method == "POST":

        form = StatusUpdateForm(request.POST)

        if form.is_valid():

            status = form.save(commit=False)
        
            status.user = request.user
         
            status.save()

    # go back to dashboard after posting
    return redirect("dashboard")


@login_required
# view to delete a notification (ajax style)
def notification_delete(request, notification_id):
    # only allow post for deleting
    if request.method != "POST":
        # return a json error if method is not post
        return JsonResponse({"error": "POST required"}, status=400)

    # find the notification that belongs to this user or return 404
    notification = get_object_or_404(
        # the model to search
        Notification,
        # match by id
        id=notification_id,
        # make sure it belongs to this user
        user=request.user
    )

    # block deletion of reminder notifications
    if "due in" in notification.title.lower():
        # return forbidden response for reminder notifications
        return JsonResponse({"error": "Reminder notifications cannot be deleted."}, status=403)

    # delete the notification from the database
    notification.delete()

    # recalculate unread notifications count
    unread_count = request.user.notifications.filter(is_read=False).count()

    # return a json success response
    return JsonResponse({
 
        "success": True,
  
        "notification_id": notification_id,

        "unread_count": unread_count,
    })