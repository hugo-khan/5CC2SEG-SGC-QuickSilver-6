from django import forms
from django.contrib.auth import authenticate


class DeleteAccountForm(forms.Form):
    """
    Form requiring explicit confirmation plus password to delete an account.

    For users who signed in with Google OAuth (no password), only confirmation is required.
    For users with passwords, both confirmation and password are required.
    """

    confirmation = forms.CharField(
        label="Type DELETE to confirm",
        widget=forms.TextInput(
            attrs={
                "placeholder": "DELETE",
                "autocorrect": "off",
                "autocapitalize": "characters",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "••••••••",
                "autocomplete": "current-password",
            }
        ),
        required=False,
    )

    def __init__(self, user=None, **kwargs):
        super().__init__(**kwargs)
        self.user = user

        # Check if user has a usable password or signed in with OAuth
        if user:
            has_password = user.has_usable_password()
            has_social_account = self._has_social_account(user)

            # If user has no password and signed in with OAuth, make password optional
            if not has_password or has_social_account:
                self.fields["password"].required = False
                self.fields["password"].widget.attrs[
                    "placeholder"
                ] = "Not required for OAuth accounts"
            else:
                self.fields["password"].required = True

    def _has_social_account(self, user):
        """Check if user has a social account (Google OAuth)."""
        try:
            from allauth.socialaccount.models import SocialAccount

            return SocialAccount.objects.filter(user=user, provider="google").exists()
        except ImportError:
            return False

    def clean_confirmation(self):
        confirmation = self.cleaned_data.get("confirmation", "")
        if confirmation.strip().upper() != "DELETE":
            raise forms.ValidationError("Please type DELETE in uppercase to continue.")
        return confirmation

    def clean(self):
        super().clean()

        # Only validate password if user has a usable password
        if self.user and self.user.has_usable_password():
            password = self.cleaned_data.get("password")
            if not password:
                self.add_error("password", "Password is required.")
                return

            user = authenticate(username=self.user.username, password=password)
            if user is None:
                self.add_error("password", "Password is incorrect.")

    def delete_user(self):
        """Delete the associated user instance."""
        if self.user is not None:
            self.user.delete()
