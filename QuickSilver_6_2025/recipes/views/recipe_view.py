##combine with actual recipe_view.py - need this function to show comments

from .forms import CommentForm

def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['form'] = CommentForm()
    return context