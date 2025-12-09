# How to Make a User an Admin in the Database

There are several ways to specify an admin user in the database. Here are the most common methods:

## Method 1: Using the Script (Easiest)

Use the provided script to make any user an admin:

```bash
# Make @johndoe an admin
python make_admin.py @johndoe

# Or use default (@johndoe)
python make_admin.py
```

## Method 2: Using Django Shell (Recommended)

### Step 1: Open Django Shell
```bash
python manage.py shell
```

### Step 2: Run these commands in the shell
```python
from recipes.models import User

# Find the user
user = User.objects.get(username='@johndoe')

# Make them a staff member (can access admin panel)
user.is_staff = True

# Make them a superuser (full admin access, bypasses all permissions)
user.is_superuser = True

# Save the changes
user.save()

# Verify
print(f"{user.username} is now an admin!")
print(f"Staff: {user.is_staff}, Superuser: {user.is_superuser}")
```

### Alternative: Make multiple users admin
```python
from recipes.models import User

# Make multiple users admin at once
usernames = ['@johndoe', '@janedoe', '@admin']
for username in usernames:
    try:
        user = User.objects.get(username=username)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"✓ Made {username} an admin")
    except User.DoesNotExist:
        print(f"✗ User {username} not found")
```

## Method 3: Using Django Admin Panel

1. **First, you need to be logged in as a superuser**
2. Go to: `http://127.0.0.1:8001/admin/`
3. Navigate to **Users** → Select a user
4. Check the boxes:
   - ✅ **Staff status** (`is_staff`)
   - ✅ **Superuser status** (`is_superuser`)
5. Click **Save**

## Method 4: Using Django Management Command

Create a custom management command (if you want to automate this):

```bash
python manage.py shell -c "
from recipes.models import User
user = User.objects.get(username='@johndoe')
user.is_staff = True
user.is_superuser = True
user.save()
print('Done!')
"
```

## Method 5: Direct Database Access (Not Recommended)

⚠️ **Warning**: Directly modifying the database is not recommended. Use Django's ORM instead.

If you must use SQL directly:
```sql
-- SQLite example
UPDATE recipes_user 
SET is_staff = 1, is_superuser = 1 
WHERE username = '@johndoe';
```

## Understanding Admin Types

### Staff Member (`is_staff = True`)
- Can access the Django admin panel
- Permissions are based on assigned permissions
- Good for limited admin access

### Superuser (`is_superuser = True`)
- Can access the Django admin panel
- **Bypasses ALL permission checks**
- Has full access to everything
- Good for full admin access

### Recommended: Both
For full admin access, set both:
```python
user.is_staff = True
user.is_superuser = True
```

## Check Who is an Admin

```python
from recipes.models import User

# List all staff members
staff = User.objects.filter(is_staff=True)
print("Staff members:")
for user in staff:
    print(f"  - {user.username}")

# List all superusers
superusers = User.objects.filter(is_superuser=True)
print("\nSuperusers:")
for user in superusers:
    print(f"  - {user.username}")

# List all admins (staff OR superuser)
admins = User.objects.filter(is_staff=True) | User.objects.filter(is_superuser=True)
print("\nAll admins:")
for user in admins.distinct():
    print(f"  - {user.username} (Staff: {user.is_staff}, Superuser: {user.is_superuser})")
```

## Create a New Admin User

If the user doesn't exist yet, create them first:

```python
from recipes.models import User

# Create a new admin user
user = User.objects.create_user(
    username='@newadmin',
    email='admin@example.com',
    password='SecurePassword123',
    first_name='Admin',
    last_name='User',
    is_staff=True,
    is_superuser=True
)
print(f"Created admin user: {user.username}")
```

Or use Django's createsuperuser command:
```bash
python manage.py createsuperuser
```

## Troubleshooting

### User not found?
```python
# List all users
from recipes.models import User
for user in User.objects.all():
    print(f"{user.username} - {user.email}")
```

### Check current admin status
```python
from recipes.models import User
user = User.objects.get(username='@johndoe')
print(f"Staff: {user.is_staff}")
print(f"Superuser: {user.is_superuser}")
```

