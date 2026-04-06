from django.db import migrations


DEMO_IMAGE_URL = (
    "https://ik.imagekit.io/uxclvasrh/Tadpole/the-lantern-tale/with-friend.jpg?updatedAt=1775470151061"
)


def seed_story(apps, schema_editor):
    Story = apps.get_model("story", "Story")
    StoryAttribute = apps.get_model("story", "StoryAttribute")
    Scene = apps.get_model("story", "Scene")
    Choice = apps.get_model("story", "Choice")

    story, _ = Story.objects.get_or_create(
        title="The Lantern Trail",
        defaults={
            "description": "A rainy night reveals a quiet house and a choice to trust the light.",
        },
    )

    StoryAttribute.objects.get_or_create(
        story=story,
        key="trust",
        defaults={"label": "Trust", "initial_value": 0},
    )
    StoryAttribute.objects.get_or_create(
        story=story,
        key="security",
        defaults={"label": "Security", "initial_value": 0},
    )

    scene_start, _ = Scene.objects.get_or_create(
        story=story,
        title="At the Gate",
        defaults={
            "content": "Rain taps the iron gate. A warm lantern glows inside the house.",
            "background_image_url": DEMO_IMAGE_URL,
            "background_image_mime": "image/png",
            "is_starting": True,
        },
    )
    scene_house, _ = Scene.objects.get_or_create(
        story=story,
        title="Inside the House",
        defaults={
            "content": "You step into the foyer. A friend offers tea and a story.",
            "background_image_url": DEMO_IMAGE_URL,
            "background_image_mime": "image/png",
        },
    )
    scene_barn, _ = Scene.objects.get_or_create(
        story=story,
        title="The Barn",
        defaults={
            "content": "You shelter in the barn as the storm settles. The night ends here.",
            "background_image_url": DEMO_IMAGE_URL,
            "background_image_mime": "image/png",
            "is_ending": True,
        },
    )

    Choice.objects.get_or_create(
        scene=scene_start,
        target_scene=scene_house,
        text="Enter the house",
        defaults={"effects": {"trust": 5}},
    )
    Choice.objects.get_or_create(
        scene=scene_start,
        target_scene=scene_barn,
        text="Stay by the barn",
        defaults={"effects": {"security": 5}},
    )
    Choice.objects.get_or_create(
        scene=scene_house,
        target_scene=scene_barn,
        text="Thank your friend and rest",
        defaults={"effects": {"trust": 10}},
    )


def clear_story(apps, schema_editor):
    Story = apps.get_model("story", "Story")
    Story.objects.filter(title="The Lantern Trail").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("story", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_story, clear_story),
    ]

