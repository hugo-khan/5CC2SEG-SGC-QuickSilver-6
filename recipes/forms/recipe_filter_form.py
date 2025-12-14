from cProfile import label

from django import forms

from recipes.models import Recipe


class RecipeFilterForm(forms.Form):
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Search by name..."}
        ),
    )

    ingredients = forms.MultipleChoiceField(
        choices=[],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Ingredients",
    )

    dietary_requirement = forms.MultipleChoiceField(
        choices=Recipe.DIETARY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Dietary Requirements",
    )

    sort_by = forms.ChoiceField(
        choices=[
            ("date", "Date Posted (Newest)"),
            ("-date", "Date Posted (Oldest)"),
            ("popularity", "Popularity (High to Low)"),
            ("-popularity", "Popularity (Low to High)"),
            ("name", "Name (A-Z)"),
        ],
        required=False,
        initial="date",
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Sort By",
    )
