from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from recipes.forms import DeleteAccountForm


@method_decorator(never_cache, name='dispatch')
class DeleteAccountView(LoginRequiredMixin, FormView):
    """
    Allow authenticated users to permanently delete their account.
    """

    template_name = 'delete_account.html'
    form_class = DeleteAccountForm
    success_url = reverse_lazy('home')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        form.delete_user()
        logout(self.request)
        messages.add_message(self.request, messages.SUCCESS, "Your account has been deleted.")
        return super().form_valid(form)

