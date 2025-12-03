from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model

from recipes.models.follow import Follow

User = get_user_model()


@login_required
def follow_user(request, user_id):
    """
    Follow a user.
    - Prevents self-follow.
    - Uses get_or_create to avoid duplicates.
    - Signals update follower/following counts automatically.
    """
    target = get_object_or_404(User, id=user_id)

    if target == request.user:
        messages.error(request, "You cannot follow yourself.")
        return redirect("profile", username=request.user.username)

    follow_obj, created = Follow.objects.get_or_create(
        follower=request.user,
        followed=target,
    )

    if created:
        messages.success(request, f"You are now following {target.username}.")
    else:
        messages.info(request, f"You are already following {target.username}.")

    return redirect("profile", username=target.username)


@login_required
def unfollow_user(request, user_id):
    """
    Unfollow a user.
    - Safe delete (won't crash if no relationship exists).
    """
    target = get_object_or_404(User, id=user_id)

    Follow.objects.filter(
        follower=request.user,
        followed=target
    ).delete()

    messages.success(request, f"You unfollowed {target.username}.")

    return redirect("profile", username=target.username)
