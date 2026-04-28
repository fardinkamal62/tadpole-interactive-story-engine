from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("story", "0003_story_background_music_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="story",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_stories",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]

