from django.contrib.admin import AdminSite
from django.contrib import messages
from django.shortcuts import redirect


class CustomAdminSite(AdminSite):
    """
    Custom admin site that blocks non-admin users from accessing the admin panel.
    """
    
    site_header = "Recipify Administration"
    site_title = "Recipify Admin"
    index_title = "Welcome to Recipify Administration"
    
    def has_permission(self, request):
        """
        Only allow staff/superusers to access the admin site.
        """
        return request.user.is_active and (request.user.is_staff or request.user.is_superuser)
    
    def index(self, request, extra_context=None):
        """
        Override the admin index to check permissions and redirect non-admins.
        """
        if not self.has_permission(request):
            if request.user.is_authenticated:
                messages.error(
                    request,
                    "Access denied. You must be a staff member or administrator to access this page."
                )
                return redirect('home')
            else:
                messages.info(
                    request,
                    "Please log in as an administrator to access the admin panel."
                )
                return redirect('admin_login')
        return super().index(request, extra_context)
    
    def login(self, request, extra_context=None):
        """
        Override admin login to redirect to our custom admin login page.
        """
        if request.user.is_authenticated:
            if request.user.is_staff or request.user.is_superuser:
                return redirect('admin:index')
            else:
                messages.error(
                    request,
                    "Access denied. You must be a staff member or administrator to access the admin panel."
                )
                return redirect('home')
        return redirect('admin_login')
