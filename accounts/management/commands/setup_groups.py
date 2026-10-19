# import the base class to create the custom django management commands
from django.core.management.base import BaseCommand

from django.contrib.auth.models import Group, Permission

# import ContentType to connect permissions to a particular model
from django.contrib.contenttypes.models import ContentType


from courses.models import Course


# create a command class so django can recognize and run this file as a command
class Command(BaseCommand):
    # message 
    help = "Create default user groups and permissions"

    # runs when the command is executed in the terminal
    def handle(self, *args, **kwargs):
        # create the teachers group if it does not exist or get it if it already there
        teachers, _ = Group.objects.get_or_create(name="Teachers")

        # create the students group if it does not exist or get it if it already there
        students, _ = Group.objects.get_or_create(name="Students")

        # get the ContentType for the Course model for permission
        course_ct = ContentType.objects.get_for_model(Course)

        # get the permission to allow to add new course
        create_course = Permission.objects.get(
            codename="add_course",
            
            content_type=course_ct,
        )

        # give teacher permission to add course 
        teachers.permissions.add(create_course)

        # print success
        self.stdout.write(self.style.SUCCESS("Groups and permissions created"))