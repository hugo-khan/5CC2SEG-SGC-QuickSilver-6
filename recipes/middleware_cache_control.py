from django.utils.deprecation import MiddlewareMixin


class NoCacheMiddleware(MiddlewareMixin):
    """
    Middleware to prevent caching of authenticated pages and logout pages.
    This prevents users from using the back button to access pages after logout.
    """
    
    def process_response(self, request, response):
        # Add no-cache headers to all authenticated pages
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        # Also add to logout and login pages
        if request.path in ['/log_out/', '/log_in/', '/admin/login/', '/sign_up/']:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response

