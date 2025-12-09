from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.views import View
from recipes.forms import LogInForm
from recipes.views.decorators import LoginProhibitedMixin


class AdminLoginView(LoginProhibitedMixin, View):
    """
    Admin login view that allows staff/superusers to log in and access the admin panel.
    This is separate from the regular user login.
    """

    http_method_names = ['get', 'post']
    redirect_when_logged_in_url = '/admin/'

    def get(self, request):
        """Display admin login form."""
        form = LogInForm()
        context = {
            'form': form,
            'is_admin_login': True,
        }
        return render(request, 'admin_login.html', context)

    def post(self, request):
        """Handle admin login submission."""
        form = LogInForm(request.POST)
        user = form.get_user()
        
        if user is not None:
            # Check if user is staff or superuser
            if user.is_staff or user.is_superuser:
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f"Welcome, {user.username}! Redirecting to admin panel...")
                return redirect('/admin/')
            else:
                messages.error(
                    request,
                    "Access denied. This login is for administrators only. "
                    "Please use the regular login page if you are not an admin."
                )
                return render(request, 'admin_login.html', {'form': form, 'is_admin_login': True})
        
        messages.error(request, "Invalid credentials or you do not have admin access.")
        return render(request, 'admin_login.html', {'form': form, 'is_admin_login': True})

