from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("story", "0002_seed_dummy_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="story",
            name="background_music_url",
            field=models.TextField(blank=True),
        ),
    ]

