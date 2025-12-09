# Admin Setup and Recipe Deletion Guide

## Setting Up an Admin User

### Create a Superuser (Admin Account)

Run this command to create an admin user with a separate login:

```bash
python manage.py createsuperuser
```

You'll be prompted for:
- Username (e.g., `admin`)
- Email address
- Password (this will be your separate admin password)

### Access the Admin Panel

1. Start your server: `python manage.py runserver 8001`
2. Go to: `http://127.0.0.1:8001/admin/`
3. Login with your admin credentials

## Admin Recipe Deletion Features

### Single Recipe Deletion

1. Go to **Recipes** in the admin panel
2. Click on any recipe to view/edit it
3. Scroll to the bottom and click **Delete**
4. Confirm deletion

### Bulk Recipe Deletion

1. Go to **Recipes** in the admin panel
2. Select multiple recipes using the checkboxes
3. Choose **"Delete selected recipes"** from the Actions dropdown
4. Click **Go**
5. Confirm the deletion

### Additional Admin Actions

- **Publish selected recipes**: Bulk publish recipes
- **Unpublish selected recipes**: Bulk unpublish recipes
- **View Recipe**: Click the "View on Site" link to see the recipe on the public site

## User Recipe Deletion

Users can delete their own recipes through the website:

1. Log in as a regular user
2. Go to any recipe they created
3. Click the **"Delete Recipe"** button
4. Confirm deletion on the confirmation page

### Security

- **Users can only delete their own recipes** - The system checks that `recipe.author == request.user`
- **Admins can delete any recipe** - Through the admin panel with their separate login
- **Non-authors cannot delete recipes** - They'll see an error message if they try

## Testing

### Test Admin Deletion

```bash
# Create a test admin user
python manage.py createsuperuser --username admin --email admin@example.com

# Or use Django shell
python manage.py shell
```

```python
from recipes.models import User
admin = User.objects.create_user(
    username='@admin',
    email='admin@example.com',
    password='AdminPassword123',
    first_name='Admin',
    last_name='User'
)
admin.is_staff = True
admin.is_superuser = True
admin.save()
```

### Test User Deletion

1. Create a regular user account
2. Create a recipe as that user
3. Try to delete it - should work
4. Try to delete another user's recipe - should fail with permission error

