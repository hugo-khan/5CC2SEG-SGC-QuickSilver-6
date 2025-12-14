#!/usr/bin/env python
"""Script to make a user an admin.
Usage: python make_admin.py [username]
Example: python make_admin.py @johndoe
"""
import os
import sys
import django


def main():
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recipify.settings')
    django.setup()

    from recipes.models import User

    # Get username from command line argument or use default
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = '@johndoe'

    # Try to find the user
    try:
        user = User.objects.get(username=username)

        # Make them admin (both staff and superuser)
        user.is_staff = True
        user.is_superuser = True
        user.save()

        print(f"✓ Successfully made {user.username} an admin!")
        print(f"  - Email: {user.email}")
        print(f"  - Full name: {user.full_name()}")
        print(f"  - Staff status: {user.is_staff}")
        print(f"  - Superuser status: {user.is_superuser}")
        print(f"\nThey can now access the admin panel at: http://127.0.0.1:8001/admin/")

    except User.DoesNotExist:
        print(f"User '{username}' not found")
        print("\nChecking for similar usernames...")
        users = User.objects.filter(username__icontains=username.replace('@', ''))
        if users:
            print("Found similar users:")
            for u in users:
                print(f"  - {u.username} (Staff: {u.is_staff}, Superuser: {u.is_superuser})")
        else:
            print(f"No users found with '{username.replace('@', '')}' in username.")
            print("\nAll users in database:")
            all_users = User.objects.all()[:20]
            if all_users:
                for u in all_users:
                    admin_status = "✓ Admin" if (u.is_staff or u.is_superuser) else "✗ Regular"
                    print(f"  - {u.username} ({admin_status})")
            else:
                print("  No users found in database.")
                print("\nTo create users, run: python manage.py seed")


if __name__ == "__main__":
    main()
