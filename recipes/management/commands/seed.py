"""
Management command to seed the database with demo data.
"""

from faker import Faker
from random import randint, choice
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from recipes.models import Recipe

# Get the custom User model
User = get_user_model()

user_fixtures = [
    {'username': '@johndoe', 'email': 'john.doe@example.org', 'first_name': 'John', 'last_name': 'Doe', 'is_staff': True},
    {'username': '@janedoe', 'email': 'jane.doe@example.org', 'first_name': 'Jane', 'last_name': 'Doe'},
    {'username': '@charlie', 'email': 'charlie.johnson@example.org', 'first_name': 'Charlie', 'last_name': 'Johnson'},
]

recipe_fixtures = [
    {
        'title': 'Classic Spaghetti Carbonara',
        'name': 'Classic Spaghetti Carbonara',
        'summary': 'Creamy pasta with pancetta and parmesan.',
        'description': 'A rich and comforting pasta made with eggs, parmesan, and crispy pancetta.',
        'ingredients': 'spaghetti, eggs, pancetta, parmesan cheese, black pepper, salt',
        'instructions': 'Cook spaghetti. Mix eggs with cheese. Cook pancetta. Combine everything while hot.',
        'cooking_time': 20,
        'difficulty': 'medium',
        'dietary_requirement': 'none',
        'popularity': 90,
    },
    {
        'title': 'Vegetable Stir Fry',
        'name': 'Vegetable Stir Fry',
        'summary': 'Colourful veggies in a quick soy-ginger sauce.',
        'description': 'A fast midweek stir fry with crisp vegetables and a savory soy-ginger glaze.',
        'ingredients': 'bell peppers, broccoli, carrots, soy sauce, garlic, ginger, rice',
        'instructions': 'Chop vegetables. Stir fry with garlic and ginger. Add soy sauce. Serve with rice.',
        'cooking_time': 15,
        'difficulty': 'easy',
        'dietary_requirement': 'vegan',
        'popularity': 75,
    },
    {
        'title': 'Chocolate Chip Cookies',
        'name': 'Chocolate Chip Cookies',
        'summary': 'Chewy cookies packed with chocolate chips.',
        'description': 'Buttery, chewy cookies dotted with plenty of chocolate chips and a hint of vanilla.',
        'ingredients': 'flour, butter, sugar, eggs, chocolate chips, vanilla extract, baking soda',
        'instructions': 'Cream butter and sugar. Add eggs and vanilla. Mix in dry ingredients. Bake at 350°F for 10-12 minutes.',
        'cooking_time': 25,
        'difficulty': 'easy',
        'dietary_requirement': 'nut_free',
        'popularity': 60,
    },
    {
        'title': 'Beef Tacos',
        'name': 'Beef Tacos',
        'summary': 'Seasoned beef tucked into crunchy shells.',
        'description': 'Taco night classic with spiced ground beef, crisp lettuce, and melty cheese.',
        'ingredients': 'ground beef, taco shells, lettuce, tomato, cheese, sour cream, taco seasoning',
        'instructions': 'Cook beef with seasoning. Warm taco shells. Assemble with toppings.',
        'cooking_time': 20,
        'difficulty': 'easy',
        'dietary_requirement': 'dairy_free',
        'popularity': 85,
    },
    {
        'title': 'Chicken Curry',
        'name': 'Chicken Curry',
        'summary': 'Creamy curry with tender chicken pieces.',
        'description': 'A mild curry simmered with coconut milk, aromatic spices, and juicy chicken.',
        'ingredients': 'chicken, curry powder, coconut milk, onions, garlic, ginger, rice',
        'instructions': 'Sauté onions, garlic, and ginger. Add chicken and curry powder. Pour in coconut milk and simmer. Serve with rice.',
        'cooking_time': 40,
        'difficulty': 'medium',
        'dietary_requirement': 'gluten_free',
        'popularity': 70,
    },
    {
        'title': 'Halloumi Power Salad',
        'name': 'Halloumi Power Salad',
        'summary': 'Hearty salad with grilled halloumi and grains.',
        'description': 'A filling bowl with chewy grains, roasted veg, and salty grilled halloumi.',
        'ingredients': 'halloumi, quinoa, roasted vegetables, spinach, lemon dressing',
        'instructions': 'Cook quinoa. Roast vegetables. Grill halloumi. Toss with spinach and dressing.',
        'cooking_time': 30,
        'difficulty': 'easy',
        'dietary_requirement': 'vegetarian',
        'popularity': 65,
    },
    {
        'title': 'Crunchy Peanut Satay Noodles',
        'name': 'Crunchy Peanut Satay Noodles',
        'summary': 'Nutty noodles with crisp veggies and tofu.',
        'description': 'Tofu and vegetables tossed in a creamy peanut satay sauce over noodles.',
        'ingredients': 'rice noodles, tofu, peanut butter, soy sauce, lime, vegetables',
        'instructions': 'Cook noodles. Stir-fry tofu and veg. Whisk satay sauce and combine.',
        'cooking_time': 25,
        'difficulty': 'medium',
        'dietary_requirement': 'none',
        'popularity': 55,
    },
]


class Command(BaseCommand):
    USER_COUNT = 20
    RECIPE_COUNT = 10
    DEFAULT_PASSWORD = 'Password123'
    help = 'Seeds the database with sample data'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.faker = Faker('en_GB')

    def handle(self, *args, **options):
        self.create_users()
        self.create_recipes()
        
        # Print summary
        users_count = User.objects.count()
        recipes_count = Recipe.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Seeding complete! Created {users_count} users and {recipes_count} recipes.'
            )
        )

    def create_users(self):
        self.generate_user_fixtures()
        self.generate_random_users()

    def create_recipes(self):
        self.generate_recipe_fixtures()
        self.generate_random_recipes()

    def generate_user_fixtures(self):
        """Create fixture users, skip if they already exist."""
        for data in user_fixtures:
            self.try_create_user(data)

    def generate_random_users(self):
        """Generate random users until the database contains USER_COUNT users."""
        user_count = User.objects.count()
        while user_count < self.USER_COUNT:
            print(f"Seeding user {user_count}/{self.USER_COUNT}", end='\r')
            self.generate_user()
            user_count = User.objects.count()
        print("User seeding complete.      ")

    def generate_user(self):
        """Generate a single random user and attempt to insert it."""
        # Keep generating until we get a unique username/email
        while True:
            first_name = self.faker.first_name()
            last_name = self.faker.last_name()
            email = create_email(first_name, last_name)
            username = create_username(first_name, last_name)
            
            # Check if this username or email already exists
            if not User.objects.filter(username=username).exists() and not User.objects.filter(email=email).exists():
                break
                
        self.try_create_user({'username': username, 'email': email, 'first_name': first_name, 'last_name': last_name})
       
    def try_create_user(self, data):
        """
        Attempt to create a user, but skip if they already exist.
        """
        # Check if user already exists BEFORE trying to create
        if User.objects.filter(username=data['username']).exists():
            self.stdout.write(
                self.style.WARNING(f"User {data['username']} already exists, skipping...")
            )
            return
            
        if User.objects.filter(email=data['email']).exists():
            self.stdout.write(
                self.style.WARNING(f"Email {data['email']} already exists, skipping...")
            )
            return

        try:                
            self.create_user(data)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to create user {data['username']}: {e}")
            )

    def create_user(self, data):
        """Create a user with the default password."""
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=Command.DEFAULT_PASSWORD,
            first_name=data['first_name'],
            last_name=data['last_name'],
        )
        
        if data.get('is_staff', False):
            user.is_staff = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f"✓ Created STAFF USER: {data['username']}")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Created user: {data['username']}")
            )

    def generate_recipe_fixtures(self):
        """Create the predefined recipe fixtures."""
        users = list(User.objects.all())
        if not users:
            self.stdout.write(self.style.ERROR("No users available to create recipes"))
            return
            
        for data in recipe_fixtures:
            self.try_create_recipe(data, users)

    def generate_random_recipes(self):
        """Generate random recipes."""
        users = list(User.objects.all())
        if not users:
            return
            
        recipe_count = Recipe.objects.count()
        while recipe_count < self.RECIPE_COUNT:
            print(f"Seeding recipe {recipe_count}/{self.RECIPE_COUNT}", end='\r')
            self.generate_recipe(users)
            recipe_count = Recipe.objects.count()
        print("Recipe seeding complete.      ")

    def generate_recipe(self, users):
        """Generate a single random recipe."""
        # Keep generating until we get a unique title
        while True:
            title = self.faker.catch_phrase()
            if not Recipe.objects.filter(title=title).exists():
                break
                
        recipe_data = {
            'title': title,
            'name': title,
            'summary': self.faker.sentence(nb_words=8),
            'description': ' '.join(self.faker.sentences(nb=2)),
            'ingredients': ', '.join(self.faker.words(nb=randint(5, 10))),
            'instructions': '. '.join(self.faker.sentences(nb=3)),
            'cooking_time': randint(10, 60),
            'difficulty': choice(['easy', 'medium', 'hard']),
            'dietary_requirement': choice([opt[0] for opt in Recipe.DIETARY_CHOICES]),
            'popularity': randint(20, 100),
            'prep_time_minutes': randint(5, 20),
            'cook_time_minutes': randint(10, 45),
            'servings': choice([2, 4, 6]),
        }
        self.try_create_recipe(recipe_data, users)

    def try_create_recipe(self, data, users):
        """Attempt to create a recipe and ignore any errors."""
        # Check if recipe already exists BEFORE trying to create
        if Recipe.objects.filter(title=data['title']).exists():
            return

        try:
            # Assign to a random user
            created_by = choice(users)
            self.create_recipe(data, created_by)
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"Failed to create recipe {data.get('title', 'Unknown')}: {e}")
            )

    def create_recipe(self, data, created_by):
        """Create a recipe with the given data."""

        title = data["title"]
        Recipe.objects.create(
            title=data["title"],
            name=data.get("name", data["title"]),
            summary=data.get("summary", data["title"]),
            description=data.get("description", data["instructions"]),
            ingredients=data["ingredients"],
            instructions=data.get("instructions", ""),
            cooking_time=data["cooking_time"],
            difficulty=data["difficulty"],
            dietary_requirement=data.get("dietary_requirement", "none"),
            popularity=data.get("popularity", randint(10, 95)),
            prep_time_minutes=data.get("prep_time_minutes"),
            cook_time_minutes=data.get("cook_time_minutes"),
            servings=data.get("servings"),
            author=created_by,
        )
        self.stdout.write(
            self.style.SUCCESS(f"✓ Created recipe: {title}")
        )

def create_username(first_name, last_name):
    return '@' + first_name.lower() + last_name.lower()

def create_email(first_name, last_name):
    return first_name + '.' + last_name + '@example.org'
