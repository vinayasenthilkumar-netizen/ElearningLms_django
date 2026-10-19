# import django's admin 
from django.contrib import admin
# import user and group models used for authentication and roles
from django.contrib.auth.models import User, Group
# import the models 
from .models import Profile, Notification
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


@admin.action(description="Change selected users to Teacher")
# selected users to the teacher role
def promote_to_teacher(modeladmin, request, queryset):
    teachers = Group.objects.get(name="Teachers")
    students = Group.objects.get(name="Students")

    # go through each selected user
    for user in queryset:
        # get or create a profile for the user, and default them to student if new
        profile, _ = Profile.objects.get_or_create(
            user=user, defaults={"role": Profile.Role.STUDENT}
        )
        # set the users role to teacher
        profile.role = Profile.Role.TEACHER
        profile.save()
        # add the user to the teachers group
        user.groups.add(teachers)
        # remove the user from the students group
        user.groups.remove(students)

@admin.action(description="Change selected users to Student")
def demote_to_student(modeladmin, request, queryset):
    # get teachers group from the database
    teachers = Group.objects.get(name="Teachers")
    # get students group from the database
    students = Group.objects.get(name="Students")
    for user in queryset:
        # get or create a profile for the user and default them to student if new
        profile, _ = Profile.objects.get_or_create(
            user=user, defaults={"role": Profile.Role.STUDENT}
        )
        # set back to student
        profile.role = Profile.Role.STUDENT
        # save the profile changes
        profile.save()

        # add to the students group
        user.groups.add(students)
        # remove the user from the teachers group
        user.groups.remove(teachers)


# register the profile model in the admin site with custom settings
@admin.register(Profile)
# admin settings for the profile model
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    # allow filtering by role
    list_filter = ("role",)


# remove the default user admin so we can register our own version
admin.site.unregister(User)

@admin.register(User)
# custom user admin that adds our promote and demote actions
class UserAdmin(BaseUserAdmin):
    list_display = ("id", "username", "email", "is_staff")
    # add the promote and demote actions to the actions dropdown
    actions = [promote_to_teacher, demote_to_student]

# register the notification model in the admin site
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    # show these columns in the notification list page
    list_display = ("id", "user", "title", "is_read", "created_at")
    # filtering by read status and date created
    list_filter = ("is_read", "created_at")