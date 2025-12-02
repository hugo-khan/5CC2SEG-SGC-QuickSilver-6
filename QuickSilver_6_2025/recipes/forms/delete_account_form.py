from django import forms
from django.contrib.auth import authenticate


class DeleteAccountForm(forms.Form):
    """
    Form requiring explicit confirmation plus password to delete an account.

    This form ensures users deliberately confirm deletion and authenticate
    with their current password before the account is removed.
    """

    confirmation = forms.CharField(
        label="Type DELETE to confirm",
        widget=forms.TextInput(
            attrs={
                'placeholder': 'DELETE',
                'autocorrect': 'off',
                'autocapitalize': 'characters',
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                'placeholder': '••••••••',
                'autocomplete': 'current-password',
            }
        ),
    )

    def __init__(self, user=None, **kwargs):
        super().__init__(**kwargs)
        self.user = user

    def clean_confirmation(self):
        confirmation = self.cleaned_data.get('confirmation', '')
        if confirmation.strip().upper() != 'DELETE':
            raise forms.ValidationError("Please type DELETE in uppercase to continue.")
        return confirmation

    def clean(self):
        super().clean()
        password = self.cleaned_data.get('password')
        if self.user is not None and password:
            user = authenticate(username=self.user.username, password=password)
        else:
            user = None
        if user is None:
            self.add_error('password', "Password is incorrect.")

    def delete_user(self):
        """Delete the associated user instance."""
        if self.user is not None:
            self.user.delete()

