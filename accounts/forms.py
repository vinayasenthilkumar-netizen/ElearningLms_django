# import django's forms module to create and customize forms
from django import forms

from django.conf import settings

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, StatusUpdate
from .models import Profile, StatusUpdate, TodoItem


# signup form that adds role and teacher code on top of the normal user creation form
class SignupForm(UserCreationForm):
    # choices shown in the role dropdown
    ROLE_CHOICES = [
        ("STUDENT", "Student"),
        ("TEACHER", "Teacher"),
    ]

    # extra fields added to the signup form
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    email = forms.EmailField(required=False)

    # role selection field with student as the default
    role = forms.ChoiceField(choices=ROLE_CHOICES, initial="STUDENT")

    # optional teacher invite code field (only needed if role is teacher)
    teacher_code = forms.CharField(
        required=False,
        help_text="Required only if you choose Teacher.",
    )

    # meta settings for which model and fields this form works with
    class Meta(UserCreationForm.Meta):
        # use the django user model
        model = User
        # include these fields in the signup form
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
            "role",
            "teacher_code",
        )

    # run extra setup when the form is created
    def __init__(self, *args, **kwargs):
        # call the parent form setup first
        super().__init__(*args, **kwargs)

        # add bootstrap classes to common input types
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.PasswordInput, forms.EmailInput, forms.Select)):
                # get any existing class value
                existing = field.widget.attrs.get("class", "")
                # add form-control to the class list
                field.widget.attrs["class"] = (existing + " form-control").strip()

        # set a nicer class specifically for the role dropdown
        self.fields["role"].widget.attrs["class"] = "form-select"

    # custom validation for the whole form
    def clean(self):
        cleaned = super().clean()
        # get the selected role
        role = cleaned.get("role")
        # get the teacher code and remove extra spaces
        code = (cleaned.get("teacher_code") or "").strip()

        # only check the code if the user selected teacher
        if role == "TEACHER":
            # read the expected code from settings
            expected = getattr(settings, "TEACHER_SIGNUP_CODE", "")
            # if no code is set in settings block teacher signup
            if not expected:
                raise forms.ValidationError("Teacher signup is not configured.")
            # if the entered code does not match show an error on teacher_code
            if code != expected:
                self.add_error("teacher_code", "Invalid teacher invite code.")

        # return the cleaned data so django can continue
        return cleaned
    

# form used for editing a user's profile details
class ProfileForm(forms.ModelForm):
    # first name field 
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    # last name field
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    # email field
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))


    class Meta:
        model = Profile
        fields = ["photo", "bio"]
        widgets = {
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "bio": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    # custom setup so we can preload values from the user object
    def __init__(self, *args, **kwargs):

        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # if we got a user, fill in initial values for the user fields
        if user:
            # set the first name starting value
            self.fields["first_name"].initial = user.first_name
            # set the last name starting value
            self.fields["last_name"].initial = user.last_name
            # set the email starting value
            self.fields["email"].initial = user.email


# form used for creating a status update
class StatusUpdateForm(forms.ModelForm):
    # meta settings for the status update form
    class Meta:
        model = StatusUpdate
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={
                "rows": 3,
                "class": "form-control",
                "placeholder": "What’s on your mind?"
            }),
        }


# form used for creating and editing todo items
class TodoForm(forms.ModelForm):
    # meta settings for the todo form
    class Meta:
        model = TodoItem
        fields = ["title", "due_date", "is_done"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Add a task..."
            }),
            "due_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
            "is_done": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }