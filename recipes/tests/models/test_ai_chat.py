from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from recipes.models import Recipe
from ai_chat.models import RecipeDraftSuggestion, ChatMessage


class RecipeDraftSuggestionTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.recipe = Recipe.objects.create(
            title="Test Recipe",
            description="Test description",
            instructions="Test instructions",
            ingredients="Test ingredients",
            prep_time_minutes=10,
            cook_time_minutes=20,
            servings=4,
            is_published=True,
            author=self.user,
        )

    def test_recipe_draft_creation(self):
        draft = RecipeDraftSuggestion.objects.create(
            user=self.user,
            prompt="Create a recipe for a vegetarian dish",
            dietary_requirements="Vegetarian",
            draft_payload={"title": "Vegetarian Salad", "ingredients": "Lettuce, Tomato, Cucumber"},
            assistant_display="A healthy vegetarian dish.",
            status=RecipeDraftSuggestion.Status.DRAFT,
        )

        self.assertEqual(draft.user, self.user)
        self.assertEqual(draft.status, RecipeDraftSuggestion.Status.DRAFT)
        self.assertEqual(draft.draft_payload["title"], "Vegetarian Salad")
        self.assertIsNone(draft.published_recipe)  # No published recipe yet
        draft.status = RecipeDraftSuggestion.Status.PUBLISHED
        draft.published_recipe = self.recipe
        draft.save()
        self.assertEqual(draft.status, RecipeDraftSuggestion.Status.PUBLISHED)
        self.assertEqual(draft.published_recipe, self.recipe)

    def test_str_method(self):
        draft = RecipeDraftSuggestion.objects.create(
            user=self.user,
            prompt="Create a new recipe",
            draft_payload={"title": "Chocolate Cake"},
            status=RecipeDraftSuggestion.Status.DRAFT,
        )
        self.assertEqual(str(draft), "Draft: Chocolate Cake (Draft)")

        draft.status = RecipeDraftSuggestion.Status.PUBLISHED
        draft.save()
        self.assertEqual(str(draft), "Draft: Chocolate Cake (Published)")

    def test_created_at(self):
        draft = RecipeDraftSuggestion.objects.create(
            user=self.user,
            prompt="Create a new recipe",
            draft_payload={"title": "Chocolate Cake"},
            status=RecipeDraftSuggestion.Status.DRAFT,
        )

        self.assertIsInstance(draft.created_at, timezone.datetime)
        self.assertLess(draft.created_at, timezone.now())

    def test_ordering_by_created_at(self):
        draft_1 = RecipeDraftSuggestion.objects.create(
            user=self.user,
            prompt="Create a new recipe",
            draft_payload={"title": "Chocolate Cake"},
            status=RecipeDraftSuggestion.Status.DRAFT,
        )

        draft_2 = RecipeDraftSuggestion.objects.create(
            user=self.user,
            prompt="Create another recipe",
            draft_payload={"title": "Vanilla Cake"},
            status=RecipeDraftSuggestion.Status.DRAFT,
        )

        drafts = RecipeDraftSuggestion.objects.all()
        self.assertEqual(drafts[0], draft_2)
        self.assertEqual(drafts[1], draft_1)


class ChatMessageTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")

        self.draft = RecipeDraftSuggestion.objects.create(
            user=self.user,
            prompt="Create a recipe for a vegetarian dish",
            draft_payload={"title": "Vegetarian Salad", "ingredients": "Lettuce, Tomato, Cucumber"},
            assistant_display="A healthy vegetarian dish.",
            status=RecipeDraftSuggestion.Status.DRAFT,
        )

    def test_chat_message_creation(self):
        message_1 = ChatMessage.objects.create(
            user=self.user,
            role=ChatMessage.Role.USER,
            content="Can you help me with a vegetarian recipe?",
            related_draft=self.draft,
        )

        message_2 = ChatMessage.objects.create(
            user=self.user,
            role=ChatMessage.Role.ASSISTANT,
            content="Sure, I can create a recipe for you.",
            related_draft=self.draft,
        )

        self.assertEqual(message_1.user, self.user)
        self.assertEqual(message_1.role, ChatMessage.Role.USER)
        self.assertEqual(message_1.content, "Can you help me with a vegetarian recipe?")
        self.assertEqual(message_1.related_draft, self.draft)

        self.assertEqual(message_2.role, ChatMessage.Role.ASSISTANT)
        self.assertEqual(message_2.content, "Sure, I can create a recipe for you.")
        self.assertEqual(message_2.related_draft, self.draft)

    def test_str_method(self):
        message = ChatMessage.objects.create(
            user=self.user,
            role=ChatMessage.Role.USER,
            content="What is your recipe suggestion?",
            related_draft=self.draft,
        )

        self.assertEqual(str(message), "[user] What is your recipe suggestion?")
        message.content = "Can you create a vegetarian recipe?"
        message.save()
        self.assertEqual(str(message), "[user] Can you create a vegetarian recipe?")

    def test_ordering_by_created_at(self):
        message_1 = ChatMessage.objects.create(
            user=self.user,
            role=ChatMessage.Role.USER,
            content="What is your recipe suggestion?",
            related_draft=self.draft,
        )

        message_2 = ChatMessage.objects.create(
            user=self.user,
            role=ChatMessage.Role.ASSISTANT,
            content="Here is my suggestion.",
            related_draft=self.draft,
        )

        messages = ChatMessage.objects.all()
        self.assertEqual(messages[0], message_1)
        self.assertEqual(messages[1], message_2)
