from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse

@login_required
def profile(request):
    """Display the current user's profile."""
    print("PROFILE VIEW IS BEING CALLED!")  # This will show in terminal
    #return HttpResponse("Profile view is working!")  # Simple test response
    return render(request, 'profile.html')