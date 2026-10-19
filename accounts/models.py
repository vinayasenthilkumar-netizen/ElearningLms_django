
from django.db import models
from django.conf import settings


# model that stores extra user info like role, photo, and bio
class Profile(models.Model):

    # role choices for users (student or teacher)
    class Role(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        TEACHER = "TEACHER", "Teacher"

    # link this profile to exactly one user account
    user = models.OneToOneField(

        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        # allow access like user.profile
        related_name="profile",
    )

    # store the users role
    role = models.CharField(max_length=10, choices=Role.choices)
    # photo upload
    photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True)
    #  bio text
    bio = models.TextField(blank=True)
    def __str__(self):
        # return username and the role label
        return f"{self.user.username} ({self.get_role_display()})"
    

# model for short status updates posted by a user
class StatusUpdate(models.Model):

    # connect each status update to a user
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="status_updates",
    )

    # store the actual status message text
    content = models.TextField()

    # save the time the status update was created
    created_at = models.DateTimeField(auto_now_add=True)

    # extra settings for this model
    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        # return username and the created date/time
        return f"{self.user.username} - {self.created_at:%Y-%m-%d %H:%M}"


# model for notifications shown to users
class Notification(models.Model):

    # connect each notification to a user
    user = models.ForeignKey(
        # use the project's user model
        settings.AUTH_USER_MODEL,
        # delete notifications if the user is deleted
        on_delete=models.CASCADE,
        # allow access like user.notifications.all()
        related_name="notifications"
    )

    # short title for the notification
    title = models.CharField(max_length=200)

    # optional longer message text
    message = models.TextField(blank=True)

    # optional link to a course related to this notification
    course = models.ForeignKey(
        # reference the course model from the courses app
        "courses.Course",
        # delete notifications if the course is deleted
        on_delete=models.CASCADE,
        # allow this field to be empty
        null=True,
        # allow this field to be blank in forms
        blank=True,
        # allow access like course.notifications.all()
        related_name="notifications"
    )

    # optional link url or path to open when clicked
    link = models.CharField(max_length=300, blank=True)

    # track whether the user has read this notification
    is_read = models.BooleanField(default=False)

    # save the time the notification was created
    created_at = models.DateTimeField(auto_now_add=True)

    # extra settings for this model
    class Meta:
        # show newest notifications first
        ordering = ["-created_at"]

    # show a readable name for this notification
    def __str__(self):
        # return username and the notification title
        return f"{self.user.username} - {self.title}"
    

# model for a user's todo list items
class TodoItem(models.Model):

    user = models.ForeignKey(
   
        settings.AUTH_USER_MODEL,

        on_delete=models.CASCADE,
        related_name="todos",
    )

    #title
    title = models.CharField(max_length=200)

    # due date for the task
    due_date = models.DateField(blank=True, null=True)

    # checkbox to mark if the task is done
    is_done = models.BooleanField(default=False)

    # save 
    created_at = models.DateTimeField(auto_now_add=True)

    # update 
    updated_at = models.DateTimeField(auto_now=True)
  
    class Meta:
      
        ordering = ["is_done", "due_date", "-created_at"]

    # show a readable name for this todo item
    def __str__(self):
        # return username and the task title
        return f"{self.user.username} - {self.title}"