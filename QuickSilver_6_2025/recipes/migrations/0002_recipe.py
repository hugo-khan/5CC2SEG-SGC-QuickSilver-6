from django.conf import settings
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=120)),
                ('summary', models.CharField(blank=True, max_length=255)),
                ('ingredients', models.TextField()),
                ('instructions', models.TextField()),
                ('prep_time_minutes', models.PositiveIntegerField(blank=True, null=True)),
                ('cook_time_minutes', models.PositiveIntegerField(blank=True, null=True)),
                ('servings', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('is_published', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='recipes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]


