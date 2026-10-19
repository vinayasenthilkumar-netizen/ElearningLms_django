
from django.contrib import admin

from .models import Course, Enrollment, Material, Feedback, Folder, BlockedStudent, Assignment, Submission


# register the course model in admin with custom settings
@admin.register(Course)
# admin settings for the course model
class CourseAdmin(admin.ModelAdmin):
    # show these columns in the course list page
    list_display = ("id", "title", "teacher", "created_at")
    # allow searching by course title and teacher username
    search_fields = ("title", "teacher__username")


# register the enrollment model in admin with custom settings
@admin.register(Enrollment)
# admin settings for the enrollment model
class EnrollmentAdmin(admin.ModelAdmin):
    # show these columns in the enrollment list page
    list_display = ("id", "course", "student", "enrolled_at")
    # allow searching by course title and student username
    search_fields = ("course__title", "student__username")


# register the folder model in admin with custom settings
@admin.register(Folder)
# admin settings for the folder model
class FolderAdmin(admin.ModelAdmin):
    # show these columns in the folder list page
    list_display = ("id", "course", "name", "order", "created_at")
    # allow searching by course title and folder name
    search_fields = ("course__title", "name")


# register the material model in admin with custom settings
@admin.register(Material)
# admin settings for the material model
class MaterialAdmin(admin.ModelAdmin):
    # show these columns in the material list page
    list_display = ("id", "course", "folder", "title", "uploaded_at")
    # allow searching by course title and material title
    search_fields = ("course__title", "title")


# register the feedback model in admin with custom settings
@admin.register(Feedback)
# admin settings for the feedback model
class FeedbackAdmin(admin.ModelAdmin):
    # show these columns in the feedback list page
    list_display = ("id", "course", "student", "rating", "created_at")
    # allow searching by course title and student username
    search_fields = ("course__title", "student__username")


# register the blocked student model in admin with custom settings
@admin.register(BlockedStudent)
# admin settings for the blocked student model
class BlockedStudentAdmin(admin.ModelAdmin):
    # show these columns in the blocked students list page
    list_display = ("id", "course", "student")


# register the assignment model in admin with custom settings
@admin.register(Assignment)
# admin settings for the assignment model
class AssignmentAdmin(admin.ModelAdmin):
    # show these columns in the assignment list page
    list_display = ("id", "title", "course", "due_date", "created_at")
    # allow searching by assignment title and course title
    search_fields = ("title", "course__title")
    # allow filtering by course in the sidebar
    list_filter = ("course",)


# register the submission model in admin with custom settings
@admin.register(Submission)
# admin settings for the submission model
class SubmissionAdmin(admin.ModelAdmin):
    # show these columns in the submission list page
    list_display = ("id", "assignment", "student", "updated_at", "grade")
    # allow searching by student, assignment title, and course title
    search_fields = ("student__username", "assignment__title", "assignment__course__title")
    # allow filtering submissions by course
    list_filter = ("assignment__course",)