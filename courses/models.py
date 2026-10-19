
from django.conf import settings
from django.db import models

from django.core.exceptions import ValidationError




# model that represents a course created by a teacher
class Course(models.Model):
    # link the course to the teacher user account
    teacher = models.ForeignKey(
        # use the project's user model
        settings.AUTH_USER_MODEL,
        # delete courses if the teacher is deleted
        on_delete=models.CASCADE,
        related_name="courses_taught",
    )
    # course title text
    title = models.CharField(max_length=200)
    # optional course description text
    description = models.TextField(blank=True)
    # time when the course was created
    created_at = models.DateTimeField(auto_now_add=True)

    # extra validation to ensure only teachers can be course owners
    def clean(self):
        # check if the teacher has a profile and the right role
        if hasattr(self.teacher, "profile") and self.teacher.profile.role != "TEACHER":
            raise ValidationError("Course teacher must have TEACHER role.")
        
    # override save so validation always runs before saving
    def save(self, *args, **kwargs):

        self.full_clean()
        # call the normal save method
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title


# model that connects a student to a course they enrolled in
class Enrollment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    student = models.ForeignKey(

        settings.AUTH_USER_MODEL,
        # delete enrollments if the student is deleted
        on_delete=models.CASCADE,
        # allow access like user.enrollments.all()
        related_name="enrollments",
    )
    # time when the student enrolled
    enrolled_at = models.DateTimeField(auto_now_add=True)

    # extra settings for this model
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["course", "student"], name="unique_enrollment")
        ]

    # extra validation to ensure only students can enroll
    def clean(self):
        # check if the student has a profile and the right role
        if hasattr(self.student, "profile") and self.student.profile.role != "STUDENT":
            raise ValidationError("Enrollment student must have STUDENT role.")
        
    # override save so validation always runs before saving
    def save(self, *args, **kwargs):
        # run full validation
        self.full_clean()
        # call the normal save method
        return super().save(*args, **kwargs)

    # show a readable name for this enrollment in admin and logs
    def __str__(self):
        return f"{self.student.username} -> {self.course.title}"


# model that groups materials into folders inside a course
class Folder(models.Model):
    # link the folder to a course
    course = models.ForeignKey(Course, related_name="folders", on_delete=models.CASCADE)
    # folder name text
    name = models.CharField(max_length=100)
    # order number for sorting folders
    order = models.PositiveIntegerField(default=0)
    # time when the folder was created
    created_at = models.DateTimeField(auto_now_add=True)

    # extra settings for this model
    class Meta:
        # order folders by order then name
        ordering = ["order", "name"]
        # prevent duplicate folder names inside the same course
        unique_together = ("course", "name")

    # show a readable name for this folder in admin and logs
    def __str__(self):
        return f"{self.course.title} - {self.name}"


# model for a file/material uploaded into a course
class Material(models.Model):
    # link the material to a course
    course = models.ForeignKey(Course, related_name="materials", on_delete=models.CASCADE)
    # optional folder link for grouping materials
    folder = models.ForeignKey(
        # connect to folder model
        Folder, related_name="materials",
        # allow folder to be empty
        null=True, blank=True,
        # if folder is deleted, keep material but remove folder link
        on_delete=models.SET_NULL
    )

    # title of the material
    title = models.CharField(max_length=200)
    # uploaded file for this material
    file = models.FileField(upload_to="materials/")
    # time when the file was uploaded
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # show a readable name for this material in admin and logs
    def __str__(self):
        return f"{self.course.title}: {self.title}"


# model for course feedback left by a student
class Feedback(models.Model):
    # link feedback to a course
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="feedback")
    # link feedback to the student who wrote it
    student = models.ForeignKey(
        # use the project's user model
        settings.AUTH_USER_MODEL,
        # delete feedback if the student is deleted
        on_delete=models.CASCADE,
        related_name="feedback_given",
    )

    rating = models.PositiveSmallIntegerField() 
    #comment text
    comment = models.TextField(blank=True)
    # time when the feedback was created
    created_at = models.DateTimeField(auto_now_add=True)

    # extra settings for this model
    class Meta:
        # prevent duplicate feedback per student per course
        constraints = [
            models.UniqueConstraint(fields=["course", "student"], name="unique_feedback")
        ]

    # show a readable name for this feedback in admin and logs
    def __str__(self):
        return f"{self.course.title} - {self.student.username} ({self.rating})"
    

# model that tracks students blocked from a course by a teacher
class BlockedStudent(models.Model):
    # link to the teacher doing the blocking
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,

        on_delete=models.CASCADE,

        related_name="blocked_students"
    )
    # link to the student being blocked
    student = models.ForeignKey(
        # use the project's user model
        settings.AUTH_USER_MODEL,
        # delete blocks if the student is deleted
        on_delete=models.CASCADE,
        # allow access like student.blocked_by.all()
        related_name="blocked_by"
    )
    # link the block to a specific course
    course = models.ForeignKey(
        # connect to course model
        Course,
        # delete blocks if the course is deleted
        on_delete=models.CASCADE,
        # allow access like course.blocked_students.all()
        related_name="blocked_students"
    )

    # show a readable name for this block in admin and logs
    def __str__(self):
        return f"{self.student.username} blocked in {self.course.title}"
    

# model for assignments inside a course
class Assignment(models.Model):
    # link assignment to a course
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    # assignment title text
    title = models.CharField(max_length=200)
    # optional instructions text
    instructions = models.TextField(blank=True)
    # optional due date/time
    due_date = models.DateTimeField(null=True, blank=True)
    # time when the assignment was created
    created_at = models.DateTimeField(auto_now_add=True)
    reminder_24h_sent = models.BooleanField(default=False)

    reminder_2h_sent = models.BooleanField(default=False)
    
    closed_notification_sent = models.BooleanField(default=False)

    # extra settings for this model
    class Meta:
        # show newest assignments first
        ordering = ["-created_at"]

    # show a readable name for this assignment in admin and logs
    def __str__(self):
        return f"{self.course.title} - {self.title}"


# model for student submissions for an assignment
class Submission(models.Model):
    # link submission to an assignment
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    # link submission to a student user account
    student = models.ForeignKey(
        # use the project's user model
        settings.AUTH_USER_MODEL,
        # delete submissions if the student is deleted
        on_delete=models.CASCADE,
        # allow access like user.submissions.all()
        related_name="submissions"
    )
    # uploaded file for the submission
    file = models.FileField(upload_to="submissions/")
    # optional note from the student
    note = models.TextField(blank=True)
    # time when the submission was first created
    submitted_at = models.DateTimeField(auto_now_add=True)
    # time when the submission was last updated
    updated_at = models.DateTimeField(auto_now=True)

    # optional teacher review fields (you can use later)
    # grade text entered by the teacher
    grade = models.CharField(max_length=20, blank=True)
    # teacher comment text entered by the teacher
    teacher_comment = models.TextField(blank=True)

    # extra settings for this model
    class Meta:
        # prevent duplicate submissions for the same assignment by the same student
        constraints = [
            models.UniqueConstraint(fields=["assignment", "student"], name="unique_submission_per_assignment")
        ]
        # show most recently updated submissions first
        ordering = ["-updated_at"]

    # show a readable name for this submission in admin and logs
    def __str__(self):
        return f"{self.assignment.title} - {self.student.username}"