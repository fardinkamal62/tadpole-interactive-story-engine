from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Story",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="Scene",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(blank=True, max_length=200)),
                ("content", models.TextField(blank=True)),
                ("background_image_url", models.TextField(blank=True)),
                ("background_image_mime", models.CharField(default="image/png", max_length=50)),
                ("is_starting", models.BooleanField(default=False)),
                ("is_ending", models.BooleanField(default=False)),
                (
                    "story",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="scenes", to="story.story"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="StoryAttribute",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=50)),
                ("label", models.CharField(max_length=100)),
                ("initial_value", models.IntegerField(default=0)),
                (
                    "story",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attributes", to="story.story"),
                ),
            ],
            options={
                "unique_together": {("story", "key")},
            },
        ),
        migrations.CreateModel(
            name="Choice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.CharField(max_length=200)),
                ("conditions", models.JSONField(blank=True, default=dict)),
                ("effects", models.JSONField(blank=True, default=dict)),
                (
                    "scene",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="choices", to="story.scene"),
                ),
                (
                    "target_scene",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="incoming_choices", to="story.scene"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PlayerState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_key", models.CharField(db_index=True, max_length=40)),
                ("attributes", models.JSONField(default=dict)),
                ("visited_scenes", models.JSONField(default=list)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "current_scene",
                    models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to="story.scene"),
                ),
                (
                    "story",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="player_states", to="story.story"),
                ),
            ],
            options={
                "unique_together": {("story", "session_key")},
            },
        ),
    ]

