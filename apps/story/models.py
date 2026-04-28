from django.db import models
from django.conf import settings


class Story(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="created_stories",
        on_delete=models.SET_NULL,
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    background_music_url = models.TextField(blank=True)

    def __str__(self):
        return self.title


class StoryAttribute(models.Model):
    story = models.ForeignKey(Story, related_name="attributes", on_delete=models.CASCADE)
    key = models.CharField(max_length=50)
    label = models.CharField(max_length=100)
    initial_value = models.IntegerField(default=0)

    class Meta:
        unique_together = ("story", "key")

    def __str__(self):
        return f"{self.story.title}: {self.key}"


class Scene(models.Model):
    story = models.ForeignKey(Story, related_name="scenes", on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField(blank=True)
    background_image_url = models.TextField(blank=True)
    background_image_mime = models.CharField(max_length=50, default="image/png")
    is_starting = models.BooleanField(default=False)
    is_ending = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.story.title} - {self.title or self.id}"


class Choice(models.Model):
    scene = models.ForeignKey(Scene, related_name="choices", on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    target_scene = models.ForeignKey(
        Scene,
        related_name="incoming_choices",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    conditions = models.JSONField(default=dict, blank=True)
    effects = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Choice {self.id} -> {self.target_scene_id}"


class PlayerState(models.Model):
    story = models.ForeignKey(Story, related_name="player_states", on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, db_index=True)
    current_scene = models.ForeignKey(Scene, null=True, on_delete=models.SET_NULL)
    attributes = models.JSONField(default=dict)
    visited_scenes = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("story", "session_key")

    def __str__(self):
        return f"{self.story.title} - {self.session_key}"
