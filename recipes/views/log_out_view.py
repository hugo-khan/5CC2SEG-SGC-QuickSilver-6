from django.contrib.auth import logout
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache


@never_cache
def log_out(request):
    """Log out the current user and prevent back button access"""
    logout(request)
    response = redirect("home")
    # Add cache control headers to prevent browser from caching the logout
    response["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response
