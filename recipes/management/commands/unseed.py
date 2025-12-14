from django.contrib.auth import get_user_model  # Updated import
from django.core.management.base import BaseCommand, CommandError

from recipes.models import Recipe

# Get the custom User model
User = get_user_model()


class Command(BaseCommand):
    """
    Management command to remove (unseed) user and recipe data from the database.
    """

    help = "Removes seeded data from the database"

    def handle(self, *args, **options):
        # Delete all recipes first (to maintain foreign key constraints)
        recipe_count, _ = Recipe.objects.all().delete()

        # Delete all non-staff users
        user_count, _ = User.objects.filter(is_staff=False).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Unseeding complete! Deleted {recipe_count} recipes and {user_count} users."
            )
        )
