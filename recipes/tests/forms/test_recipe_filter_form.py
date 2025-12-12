from django.test import TestCase
from recipes.forms import RecipeFilterForm
from recipes.models import Recipe


class RecipeFilterFormTests(TestCase):

    def test_form_fields_exist(self):
        form = RecipeFilterForm()

        self.assertIn("search", form.fields)
        self.assertIn("dietary_requirement", form.fields)
        self.assertIn("sort_by", form.fields)

    def test_search_field_properties(self):
        form = RecipeFilterForm()

        search = form.fields["search"]

        self.assertEqual(search.max_length, 100)
        self.assertFalse(search.required)
        self.assertEqual(search.widget.attrs["placeholder"], "Search by name...")
        self.assertEqual(search.widget.attrs["class"], "form-control")

    def test_dietary_requirement_field_properties(self):
        form = RecipeFilterForm()
        field = form.fields["dietary_requirement"]

        self.assertFalse(field.required)
        self.assertEqual(field.choices, Recipe.DIETARY_CHOICES)
        self.assertEqual(field.widget.__class__.__name__, "CheckboxSelectMultiple")

    def test_sort_by_field_properties(self):
        form = RecipeFilterForm()
        field = form.fields["sort_by"]

        expected_choices = [
            ('date', 'Date Posted (Newest)'),
            ('-date', 'Date Posted (Oldest)'),
            ('popularity', 'Popularity (High to Low)'),
            ('-popularity', 'Popularity (Low to High)'),
            ('name', 'Name (A-Z)'),
        ]

        self.assertEqual(field.choices, expected_choices)
        self.assertFalse(field.required)
        self.assertEqual(field.initial, "date")
        self.assertEqual(field.widget.attrs["class"], "form-control")

    def test_form_is_valid_with_no_data(self):
        #empty filtering
        form = RecipeFilterForm(data={})
        self.assertTrue(form.is_valid())

    def test_form_is_valid_with_full_data(self):
        form = RecipeFilterForm(data={
            "search": "chocolate",
            "dietary_requirement": [choice[0] for choice in Recipe.DIETARY_CHOICES[:2]],
            "sort_by": "name",
        })

        self.assertTrue(form.is_valid())
        cleaned = form.cleaned_data

        self.assertEqual(cleaned["search"], "chocolate")
        self.assertEqual(cleaned["sort_by"], "name")
        self.assertListEqual(
            cleaned["dietary_requirement"],
            [Recipe.DIETARY_CHOICES[0][0], Recipe.DIETARY_CHOICES[1][0]]
        )

