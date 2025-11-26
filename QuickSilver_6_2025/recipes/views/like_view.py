from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from recipes.models import Recipe, Like

@method_decorator(login_required, name="dispatch")
class ToggleLikeView(View):
    def post(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, id=recipe_id)
        like, created = Like.objects.get_or_create(user=request.user, recipe=recipe)

        if not created:
            # Already liked → Unlike
            like.delete()

        return redirect("recipe_detail", recipe_id)