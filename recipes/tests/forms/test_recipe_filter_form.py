"""Tests for RecipeFilterForm."""
from django.test import TestCase

from recipes.forms.recipe_filter_form import RecipeFilterForm


class RecipeFilterFormTest(TestCase):
    def test_form_has_search_field(self):
        """Test that form has search field."""
        form = RecipeFilterForm()
        self.assertIn('search', form.fields)

    def test_form_has_dietary_requirement_field(self):
        """Test that form has dietary_requirement field."""
        form = RecipeFilterForm()
        self.assertIn('dietary_requirement', form.fields)

    def test_form_has_sort_by_field(self):
        """Test that form has sort_by field."""
        form = RecipeFilterForm()
        self.assertIn('sort_by', form.fields)

    def test_form_search_is_optional(self):
        """Test that search field is optional."""
        form = RecipeFilterForm(data={})
        self.assertTrue(form.is_valid())

    def test_form_with_search_term(self):
        """Test that form accepts search term."""
        form = RecipeFilterForm(data={'search': 'pasta'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['search'], 'pasta')

    def test_form_with_dietary_requirement(self):
        """Test that form accepts dietary requirement filter."""
        form = RecipeFilterForm(data={'dietary_requirement': ['vegan', 'vegetarian']})
        self.assertTrue(form.is_valid())

    def test_form_with_sort_by(self):
        """Test that form accepts sort_by option."""
        form = RecipeFilterForm(data={'sort_by': 'popularity'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['sort_by'], 'popularity')

    def test_form_default_sort_by(self):
        """Test that form has default sort_by value."""
        form = RecipeFilterForm()
        self.assertEqual(form.fields['sort_by'].initial, 'date')

