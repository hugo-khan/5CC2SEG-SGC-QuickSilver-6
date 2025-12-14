from django.contrib import messages
from django.shortcuts import redirect


class AdminAccessMiddleware:
    """
    Middleware to block non-admin users from accessing the Django admin panel.
    Note: This middleware must be placed AFTER MessageMiddleware in settings.MIDDLEWARE
    to use messages.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the request is for the admin panel
        if request.path.startswith("/admin/"):
            # Allow access to admin login and logout pages (Django's built-in)
            # Also allow our custom admin login page
            if (
                request.path == "/admin/login/"
                or request.path == "/admin/logout/"
                or request.path == "/admin/login"
                or request.path == "/admin/logout"
            ):
                response = self.get_response(request)
                return response

            # For all other admin paths, check permissions
            if not request.user.is_authenticated:
                messages.info(
                    request,
                    "Please log in as an administrator to access the admin panel.",
                )
                return redirect("admin_login")

            if not (request.user.is_staff or request.user.is_superuser):
                messages.error(
                    request,
                    "Access denied. You must be a staff member or administrator to access the admin panel.",
                )
                return redirect("home")

        response = self.get_response(request)
        return response
