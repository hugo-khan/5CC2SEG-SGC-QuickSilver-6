from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from recipes.models.recipe import Recipe
from recipes.models.like import Like
from recipes.models.saved_recipes import SavedRecipe
from recipes.models.comment import Comment
from recipes.models.follow import Follow
from recipes.models.tag import Tag

User = get_user_model()


class Command(BaseCommand):
    help = "Clear ALL seeded data (users, recipes, tags, interactions)."

    def handle(self, *args, **options):
        self.stdout.write("Unseeding...")

        Comment.objects.all().delete()
        Like.objects.all().delete()
        SavedRecipe.objects.all().delete()
        Follow.objects.all().delete()
        Recipe.objects.all().delete()
        Tag.objects.all().delete()
        User.objects.filter(is_staff=False, is_superuser=False).delete()

        self.stdout.write(self.style.SUCCESS("Database unseeded."))
