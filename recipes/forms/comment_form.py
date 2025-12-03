from recipes.models import Comment
from django import forms

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        #user input - the time stamp is done by the system not the user so not present
        fields = ['text']
        widgets = {'text': forms.Textarea(attrs={
            'rows': 5,
            'style':'resize: vertical; width 100%',
            'placeholder': 'Add a comment about this recipe...',
            'class': 'form-control'}),}
        labels = {'text': 'Your Comment'}
