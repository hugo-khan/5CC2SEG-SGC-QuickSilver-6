from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache # New Import


@login_required
@never_cache # Apply anti-caching decorator
def dashboard(request):
    """Display welcome page for logged-in users."""
    return render(request, "dashboard.html", {"user": request.user})