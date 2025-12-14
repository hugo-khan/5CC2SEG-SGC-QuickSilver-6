from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic.edit import FormView

from recipes.forms import DeleteAccountForm


@method_decorator(never_cache, name="dispatch")
class DeleteAccountView(LoginRequiredMixin, FormView):
    """
    Allow authenticated users to permanently delete their account.
    Handles both password-based and OAuth (Google) accounts.
    """

    template_name = "delete_account.html"
    form_class = DeleteAccountForm
    success_url = reverse_lazy("home")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"user": self.request.user})
        return kwargs

    def get_context_data(self, **kwargs):
        """Add context about whether user has password or OAuth account."""
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Check if user has a usable password
        has_password = user.has_usable_password()

        # Check if user has Google OAuth account
        has_google_account = False
        try:
            from allauth.socialaccount.models import SocialAccount

            has_google_account = SocialAccount.objects.filter(
                user=user, provider="google"
            ).exists()
        except ImportError:
            pass

        context["has_password"] = has_password
        context["has_google_account"] = has_google_account
        context["is_oauth_user"] = has_google_account or not has_password

        return context

    def form_valid(self, form):
        form.delete_user()
        logout(self.request)
        messages.add_message(
            self.request, messages.SUCCESS, "Your account has been deleted."
        )
        return super().form_valid(form)
