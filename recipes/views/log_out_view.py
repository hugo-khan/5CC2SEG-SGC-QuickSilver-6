from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache # New Import


@never_cache # Apply anti-caching decorator
def log_out(request):
    """Log out the current user"""

    logout(request)
    return redirect('home')