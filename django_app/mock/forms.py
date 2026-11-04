from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


class SignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, label="First name(s)")
    last_name = forms.CharField(max_length=150, label="Last name(s)")
    email = forms.EmailField(label="Email address")
    email_confirm = forms.EmailField(label="Confirm email address")
    phone = forms.CharField(max_length=32, required=False, label="Phone (optional)")
    results_consent = forms.BooleanField(
        required=True,
        label="I agree that my test results will be saved to this account.",
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields((
            "first_name", "last_name", "email", "email_confirm", "phone",
            "username", "password1", "password2", "results_consent",
        ))
        self.fields["username"].help_text = "Used to log in to your account."

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        email_confirm = cleaned_data.get("email_confirm")
        if email and email_confirm and email.casefold() != email_confirm.casefold():
            self.add_error("email_confirm", "Email addresses do not match.")
        return cleaned_data