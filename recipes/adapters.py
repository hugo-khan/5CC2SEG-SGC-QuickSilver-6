import string
import secrets
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()


class RecipeAccountAdapter(DefaultAccountAdapter):
    """
    Custom adapter that manually generates a unique username conforming to 
    the custom '@\\w{3,}' regex and ensures a unique username is created.
    """
    
    def populate_username(self, request, user):
        """
        Manually sets a valid, unique username based on the user's email address.
        """
        # Only populate if username is not already set
        if user.username:
            return
        
        # Get email from user or social account data
        email = user.email
        if not email and hasattr(user, 'socialaccount_set'):
            social_accounts = user.socialaccount_set.all()
            if social_accounts:
                email = social_accounts[0].extra_data.get('email', '')
        
        # Fallback if no email is available
        if not email:
            email = f"user{secrets.token_hex(4)}@example.com"
        
        # 1. Get the local part of the email (e.g., 'ameytrip')
        email_local_part = email.split('@')[0]
        
        # 2. Sanitize to only keep valid word characters
        sanitized_base = ''.join(c for c in email_local_part if c.isalnum() or c == '_')
        
        # 3. Ensure the base name is long enough for the @\\w{3,} regex
        if len(sanitized_base) < 3:
             sanitized_base = 'user'
             
        # 4. Construct the initial username with the required '@' prefix
        base_username = '@' + sanitized_base
        
        # 5. Find a guaranteed unique version of the base_username in the database
        user.username = self._create_unique_username(base_username)
    
    def generate_unique_username(self, txts, regex=None):
        """
        Override the default generate_unique_username to use our custom logic.
        This prevents the NotImplementedError from allauth's default implementation.
        """
        # Extract email from txts (usually a list of strings)
        email = None
        for txt in txts:
            if '@' in str(txt):
                email = str(txt)
                break
        
        if not email:
            # Fallback to generating a random username
            random_suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
            base_username = '@user' + random_suffix
        else:
            # Use the same logic as populate_username
            email_local_part = email.split('@')[0]
            sanitized_base = ''.join(c for c in email_local_part if c.isalnum() or c == '_')
            if len(sanitized_base) < 3:
                sanitized_base = 'user'
            base_username = '@' + sanitized_base
        
        return self._create_unique_username(base_username)

    
    def _create_unique_username(self, base_username):
        """
        Manually checks for uniqueness and appends a number/random suffix 
        to the provided base_username until a free one is found.
        """
        
        # Use max_length=30 as defined in the User model
        max_len = 30 
        
        i = 0
        
        # Remove the @ prefix for length calculation
        base_prefix = base_username.lstrip('@')
        
        while True:
            # Generate a suffix
            if i == 0:
                suffix = ''
            else:
                # Use a counter (e.g., '1', '2', etc.)
                suffix = str(i)
                
            # Check the available space for the prefix before the suffix is added
            # -1 is for the required '@' symbol
            available_prefix_length = max_len - 1 - len(suffix)
            
            candidate_prefix = base_prefix
            
            if len(base_prefix) > available_prefix_length:
                candidate_prefix = base_prefix[:available_prefix_length]

            candidate_username = '@' + candidate_prefix + suffix
            
            # Check database for collision
            if not User.objects.filter(username=candidate_username).exists():
                return candidate_username
            
            i += 1
            # Hard safety break to prevent an infinite loop
            if i > 500:
                # Fallback to generating a purely random, valid username
                random_suffix = ''.join(secrets.choice(string.ascii_letters + string.digits) for j in range(max_len - 1))
                return '@' + random_suffix[:max_len-1]

