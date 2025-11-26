import pytest
from django.urls import reverse
from recipes.models.comment import Comment
from recipes.models.recipe import Recipe
from recipes.models.user import User
from recipes.forms.comment_form import CommentForm


# COMMENT CREATION TESTS


@pytest.mark.django_db
def test_logged_in_user_can_post_comment(client):
    user = User.objects.create_user(username="alice", password="pass123")
    recipe = Recipe.objects.create(title="Soup Test", user=user)

    client.login(username="alice", password="pass123")

    url = reverse("add_comment", args=[recipe.id])
    response = client.post(url, {"text": "Great recipe!"})

    assert response.status_code == 302
    assert Comment.objects.count() == 1

    c = Comment.objects.first()
    assert c.text == "Great recipe!"
    assert c.recipe == recipe
    assert c.user == user


@pytest.mark.django_db
def test_anonymous_user_cannot_post_comment(client):
    user = User.objects.create(username="bob")
    recipe = Recipe.objects.create(title="Pancakes", user=user)

    url = reverse("add_comment", args=[recipe.id])
    response = client.post(url, {"text": "Nice!"})

    # Should redirect to login
    assert response.status_code == 302
    assert "/login" in response.url
    assert Comment.objects.count() == 0


# FORM VALIDATION TESTS


@pytest.mark.django_db
def test_comment_form_rejects_empty_text():
    form = CommentForm(data={"text": ""})
    assert not form.is_valid()
    assert "text" in form.errors


@pytest.mark.django_db
def test_comment_form_accepts_valid_text():
    form = CommentForm(data={"text": "Tasty!"})
    assert form.is_valid()



# RECIPE PAGE COMMENT DISPLAY TESTS


@pytest.mark.django_db
def test_recipe_page_displays_all_comments(client):
    user = User.objects.create(username="carol")
    recipe = Recipe.objects.create(title="Stew", user=user)

    comments = []
    for t in ["one", "two", "three", "four"]:
        comments.append(Comment.objects.create(recipe=recipe, user=user, text=t))

    url = reverse("recipe_detail", args=[recipe.id])
    response = client.get(url)

    assert response.status_code == 200
    assert "comments" in response.context

    returned = response.context["comments"]

    assert len(returned) == 4
    # newest first
    assert returned[0].text == "four"
    assert returned[-1].text == "one"



# FEED PAGE TOP-3 COMMENT TESTS


@pytest.mark.django_db
def test_feed_shows_only_top_three_comments(client):
    user = User.objects.create(username="dave")
    recipe = Recipe.objects.create(title="Cake", user=user)

    # Create 5 comments: comment 0 ... comment 4
    for i in range(5):
        Comment.objects.create(recipe=recipe, user=user, text=f"Comment {i}")

    response = client.get(reverse("feed"))
    assert response.status_code == 200

    # Feed templates typically pass comments grouped by recipe
    comments_by_recipe = response.context["comments"]
    comments = comments_by_recipe[recipe.id]

    assert len(comments) == 3

    # Top 3 = newest: 4, 3, 2
    assert comments[0].text == "Comment 4"
    assert comments[1].text == "Comment 3"
    assert comments[2].text == "Comment 2"


# MODAL EXISTENCE TEST


@pytest.mark.django_db
def test_comment_modal_exists_in_recipe_page(client):
    user = User.objects.create(username="emily")
    recipe = Recipe.objects.create(title="Salad", user=user)

    response = client.get(reverse("recipe_detail", args=[recipe.id]))
    assert response.status_code == 200

    html = response.content.decode()

    # Modal container
    assert 'id="commentModal"' in html
    assert 'class="modal fade"' in html

    # Form tag
    assert "<form" in html
    assert "add_comment" in html  # action URL correct

    # Should contain textarea
    assert "<textarea" in html
    assert "name=\"text\"" in html


# COMMENT ORDERING TEST


@pytest.mark.django_db
def test_comment_ordering_newest_first(client):
    user = User.objects.create(username="frank")
    recipe = Recipe.objects.create(title="Burger", user=user)

    Comment.objects.create(recipe=recipe, user=user, text="Oldest")
    Comment.objects.create(recipe=recipe, user=user, text="Middle")
    Comment.objects.create(recipe=recipe, user=user, text="Newest")

    response = client.get(reverse("recipe_detail", args=[recipe.id]))

    comments = response.context["comments"]

    # Should return: Newest, Middle, Oldest
    assert comments[0].text == "Newest"
    assert comments[1].text == "Middle"
    assert comments[2].text == "Oldest"
