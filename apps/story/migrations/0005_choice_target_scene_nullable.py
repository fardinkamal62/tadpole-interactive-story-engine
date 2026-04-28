from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("story", "0004_story_owner"),
    ]

    operations = [
        migrations.AlterField(
            model_name="choice",
            name="target_scene",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name="incoming_choices",
                to="story.scene",
            ),
        ),
    ]

