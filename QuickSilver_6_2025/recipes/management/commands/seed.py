"""
Seeder updated to include:
- Tags
- Recipe difficulty
- Faker images
- Full fixture-preserved user list
- Likes, Saves, Comments, Follows
- Random tag assignment
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
from random import sample, randint

from recipes.models.recipe import Recipe
from recipes.models.like import Like
from recipes.models.saved_recipes import SavedRecipe
from recipes.models.comment import Comment
from recipes.models.follow import Follow
from recipes.models.tag import Tag

User = get_user_model()
fake = Faker()

# Preserved user fixtures
user_fixtures = [
    {"username": "@johndoe", "email": "john.doe@example.org", "first_name": "John", "last_name": "Doe", "is_staff": True},
    {"username": "@janedoe", "email": "jane.doe@example.org", "first_name": "Jane", "last_name": "Doe"},
    {"username": "@petrapickles", "email": "petrapickles@example.org", "first_name": "Petra", "last_name": "Pickles"},
    {"username": "@peterpickles", "email": "peterpickles@example.org", "first_name": "Peter", "last_name": "Pickles"},
]

# Industry-standard tags
RECIPE_TAGS = [
    "vegetarian", "vegan", "gluten-free", "dairy-free", "keto", "paleo",
    "breakfast", "lunch", "dinner", "dessert", "snack",
    "quick", "healthy", "high-protein", "low-carb",
    "salad", "soup", "pasta", "seafood", "chicken", "beef",
]


class Command(BaseCommand):
    help = "Seed the database with demo data including tags and difficulty."

    def handle(self, *args, **options):
        self.stdout.write("Clearing database...")

        # FK-safe deletion order
        Comment.objects.all().delete()
        Like.objects.all().delete()
        SavedRecipe.objects.all().delete()
        Follow.objects.all().delete()
        Recipe.objects.all().delete()
        Tag.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()

        self.stdout.write("Creating users...")
        users = []
        for u in user_fixtures:
            user = User.objects.create_user(
                username=u["username"],
                email=u["email"],
                first_name=u.get("first_name", ""),
                last_name=u.get("last_name", ""),
                password="password123",
                is_staff=u.get("is_staff", False),
            )
            users.append(user)

        self.stdout.write("Creating tags...")
        tags = []
        for tag_name in RECIPE_TAGS:
            tag = Tag.objects.create(name=tag_name)
            tags.append(tag)

        self.stdout.write("Creating recipes...")

        recipes = []
        for user in users:
            for _ in range(randint(2, 4)):
                recipe = Recipe.objects.create(
                    user=user,
                    title=fake.sentence(nb_words=4),
                    description=fake.paragraph(nb_sentences=3),
                    instructions=fake.text(max_nb_chars=400),
                    cooking_time=randint(10, 120),
                    servings=randint(1, 8),
                    difficulty=sample(["easy", "medium", "hard"], 1)[0],
                    image=f"https://picsum.photos/seed/{fake.uuid4()}/600/400",
                )

                recipe.tags.set(sample(tags, randint(1, 4)))
                recipes.append(recipe)

        self.stdout.write("Creating follows, likes, saves, comments...")

        for recipe in recipes:
            actors = sample(users, randint(1, len(users)))

            for u in actors:
                Like.objects.get_or_create(user=u, recipe=recipe)
                SavedRecipe.objects.get_or_create(user=u, recipe=recipe)
                Comment.objects.create(user=u, recipe=recipe, text=fake.sentence())

            # Random follows
            follow_targets = sample(users, randint(0, len(users)))
            for ft in follow_targets:
                if ft != recipe.user:
                    Follow.objects.get_or_create(follower=recipe.user, followed=ft)

        self.stdout.write(self.style.SUCCESS("Database seeded successfully!"))
