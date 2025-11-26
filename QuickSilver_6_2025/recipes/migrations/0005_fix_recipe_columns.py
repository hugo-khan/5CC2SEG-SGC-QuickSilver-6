from django.db import migrations, models


def add_missing_recipe_fields(apps, schema_editor):
    """
    Ensure the existing recipes_recipe table has the columns expected
    by the current Recipe model without dropping any data.
    """
    connection = schema_editor.connection
    cursor = connection.cursor()

    table_name = "recipes_recipe"

    # Introspect existing columns in the table
    existing_columns = {
        col.name for col in connection.introspection.get_table_description(cursor, table_name)
    }

    Recipe = apps.get_model("recipes", "Recipe")

    # Add cooking_time column if it's missing
    if "cooking_time" not in existing_columns:
        field = models.PositiveIntegerField(
            default=0,
            help_text="Cooking time in minutes",
        )
        field.set_attributes_from_name("cooking_time")
        schema_editor.add_field(Recipe, field)

    # Add difficulty column if it's missing
    if "difficulty" not in existing_columns:
        field = models.CharField(
            max_length=10,
            choices=[
                ("easy", "Easy"),
                ("medium", "Medium"),
                ("hard", "Hard"),
            ],
            default="easy",
        )
        field.set_attributes_from_name("difficulty")
        schema_editor.add_field(Recipe, field)


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0004_merge_0003_follow_0003_savedrecipe"),
    ]

    operations = [
        migrations.RunPython(
            add_missing_recipe_fields,
            migrations.RunPython.noop,
        ),
    ]


