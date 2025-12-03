# recipes/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models.user import User
from .models.recipe import Recipe
from .models.follow import Follow
from .models.like import Like
from .models.saved_recipes import SavedRecipe
from .models.comment import Comment


# -------------------------
# FOLLOW: followers / following counts
# -------------------------

@receiver(post_save, sender=Follow)
def update_follow_counts_on_create(sender, instance, created, **kwargs):
    if created:
        # follower → their following_count increases
        follower = instance.follower
        follower.following_count = Follow.objects.filter(follower=follower).count()
        follower.save(update_fields=["following_count"])

        # followed → their followers_count increases
        followed = instance.followed
        followed.followers_count = Follow.objects.filter(followed=followed).count()
        followed.save(update_fields=["followers_count"])


@receiver(post_delete, sender=Follow)
def update_follow_counts_on_delete(sender, instance, **kwargs):
    follower = instance.follower
    follower.following_count = Follow.objects.filter(follower=follower).count()
    follower.save(update_fields=["following_count"])

    followed = instance.followed
    followed.followers_count = Follow.objects.filter(followed=followed).count()
    followed.save(update_fields=["followers_count"])


# -------------------------
# LIKE: likes_count
# -------------------------

@receiver(post_save, sender=Like)
def update_likes_count_on_create(sender, instance, created, **kwargs):
    if created:
        recipe = instance.recipe
        recipe.likes_count = Like.objects.filter(recipe=recipe).count()
        recipe.save(update_fields=["likes_count"])


@receiver(post_delete, sender=Like)
def update_likes_count_on_delete(sender, instance, **kwargs):
    recipe = instance.recipe
    recipe.likes_count = Like.objects.filter(recipe=recipe).count()
    recipe.save(update_fields=["likes_count"])


# -------------------------
# SAVED RECIPE: saves_count
# -------------------------

@receiver(post_save, sender=SavedRecipe)
def update_saves_count_on_create(sender, instance, created, **kwargs):
    if created:
        recipe = instance.recipe
        recipe.saves_count = SavedRecipe.objects.filter(recipe=recipe).count()
        recipe.save(update_fields=["saves_count"])


@receiver(post_delete, sender=SavedRecipe)
def update_saves_count_on_delete(sender, instance, **kwargs):
    recipe = instance.recipe
    recipe.saves_count = SavedRecipe.objects.filter(recipe=recipe).count()
    recipe.save(update_fields=["saves_count"])


# -------------------------
# COMMENT: comments_count
# -------------------------

@receiver(post_save, sender=Comment)
def update_comments_count_on_create(sender, instance, created, **kwargs):
    if created:
        recipe = instance.recipe
        recipe.comments_count = Comment.objects.filter(recipe=recipe).count()
        recipe.save(update_fields=["comments_count"])


@receiver(post_delete, sender=Comment)
def update_comments_count_on_delete(sender, instance, **kwargs):
    recipe = instance.recipe
    recipe.comments_count = Comment.objects.filter(recipe=recipe).count()
    recipe.save(update_fields=["comments_count"])
