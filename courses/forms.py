
from django import forms

from .models import Feedback


# form used for students to leave feedback on a course
class FeedbackForm(forms.ModelForm):
    # rating field with limits from 1 to 5
    rating = forms.IntegerField(min_value=1, max_value=5)

    # meta settings for how this form connects to the feedback model
    class Meta:
        # set the model this form is based on
        model = Feedback
        # include these fields in the form
        fields = ["rating", "comment"]
        # customize the comment field widget styling
        widgets = {
            # use a textarea with bootstrap styling for the comment
            "comment": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }