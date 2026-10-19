
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile
User = get_user_model()


# connect this function to run after a user is saved
@receiver(post_save, sender=User)
# create a profile and assign the default group when a new user is created
def create_profile_and_assign_group(sender, instance, created, **kwargs):
    if not created:
        return
    students_group, _ = Group.objects.get_or_create(name="Students")
    Group.objects.get_or_create(name="Teachers")

    # create a profile for the new user and default their role to student
    Profile.objects.get_or_create(
        user=instance,
        defaults={"role": Profile.Role.STUDENT}
    )

    # if the user has no groups yet, add them to the students group
    if not instance.groups.exists():
        instance.groups.add(students_group)