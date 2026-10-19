# import path so we can define url routes
from django.urls import path

# import the views file so we can connect urls to view functions
from . import views

app_name = "courses"


# list of url patterns for the courses app
urlpatterns = [
    # route for the courses list page
    path("", views.course_list, name="list"),

    # route for creating a new course
    path("create/", views.course_create, name="create"),

    # route for editing a  course
    path("<int:course_id>/edit/", views.course_edit, name="edit"),

    # route for deleteing a course
    path("<int:course_id>/delete/", views.course_delete, name="delete"),

    # route for viewing a single course detail page
    path("<int:course_id>/", views.course_detail, name="detail"),

    # route for enrolling in a course
    path("<int:course_id>/enroll/", views.enroll_course, name="enroll"),

    # route for adding course materials
    path("<int:course_id>/materials/add/", views.material_add, name="material_add"),

    # route for creating a folder inside a course
    path("course/<int:course_id>/folder/create/", views.create_folder, name="folder_create"),

    # route for removing a student from a course
    path("course/<int:course_id>/remove/<int:student_id>/", views.remove_student, name="remove_student"),

    # route for blocking a student from a course
    path("course/<int:course_id>/block/<int:student_id>/", views.block_student, name="block_student"),

    # route for unblocking a student from a course
    path("<int:course_id>/unblock/<int:student_id>/", views.unblock_student, name="unblock_student"),

    # route for deleting a material file
    path("course/<int:course_id>/material/<int:material_id>/delete/", views.material_delete, name="material_delete"),

    # route for deleting a folder
    path("course/<int:course_id>/folder/<int:folder_id>/delete/", views.folder_delete, name="folder_delete"),

    # route for submitting course feedback
    path("course/<int:course_id>/feedback/", views.feedback_submit, name="feedback_submit"),

    # route for viewing submissions page for a course
    path("course/<int:course_id>/submissions/", views.submissions_page, name="submissions_page"),

    # route for creating a new assignment
    path("course/<int:course_id>/assignments/create/", views.assignment_create, name="assignment_create"),

    # route for students to submit work for an assignment
    path("course/<int:course_id>/assignments/<int:assignment_id>/submit/", views.submission_upload, name="submission_upload"),

    # route for teachers to grade a submission
    path("course/<int:course_id>/submissions/<int:submission_id>/grade/", views.submission_grade, name="submission_grade"),

    # route for editing an assignment
    path("course/<int:course_id>/assignments/<int:assignment_id>/edit/", views.assignment_edit, name="assignment_edit"),

    # route for deleting an assignment
    path("course/<int:course_id>/assignments/<int:assignment_id>/delete/", views.assignment_delete, name="assignment_delete"),

    # route for opening the course whiteboard page
    path("<int:course_id>/whiteboard/", views.whiteboard_page, name="whiteboard"),
]