# management/commands/checkdb.py (Simple version)
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from recipes.models import Recipe


class Command(BaseCommand):
    help = "Quick database summary"

    def handle(self, *args, **options):
        User = get_user_model()

        users = User.objects.all()
        recipes = Recipe.objects.all()

        self.stdout.write("=== DATABASE SUMMARY ===")

        # Users
        self.stdout.write(f"\nUSERS: {users.count()} total")
        self.stdout.write(f"  Superusers: {users.filter(is_superuser=True).count()}")
        self.stdout.write(f"  Staff: {users.filter(is_staff=True).count()}")

        superusers = users.filter(is_superuser=True)
        if superusers.exists():
            self.stdout.write(f"\n  Superuser accounts:")
            for user in superusers:
                self.stdout.write(f"    - {user.username} ({user.email})")

        # Recipes
        self.stdout.write(f"\nRECIPES: {recipes.count()} total")
        self.stdout.write(f"  Easy: {recipes.filter(difficulty='easy').count()}")
        self.stdout.write(f"  Medium: {recipes.filter(difficulty='medium').count()}")
        self.stdout.write(f"  Hard: {recipes.filter(difficulty='hard').count()}")

        # Sample recipes
        if recipes.exists():
            self.stdout.write(f"\n  Sample recipes:")
            for recipe in recipes[:3]:
                self.stdout.write(
                    f"    - '{recipe.title}' by {recipe.created_by.username}"
                )
