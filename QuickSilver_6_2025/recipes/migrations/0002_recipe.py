from django.conf import settings
from django.db import migrations, models
import django.utils.timezone
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('summary', models.CharField(blank=True, max_length=255)),
                ('ingredients', models.TextField(help_text='List ingredients separated by commas')),
                ('instructions', models.TextField()),
                ('prep_time_minutes', models.PositiveIntegerField(blank=True, null=True)),
                ('cook_time_minutes', models.PositiveIntegerField(blank=True, null=True)),
                ('servings', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('is_published', models.BooleanField(default=True)),
                ('cooking_time', models.PositiveIntegerField(default=0, help_text='Cooking time in minutes')),
                ('difficulty', models.CharField(choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')], default='easy', max_length=10)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
