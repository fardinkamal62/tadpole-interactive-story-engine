from django.db import models
from django.contrib.auth.models import User

class Story(models.Model):
    title = models.CharField(max_length=200)
    theme = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.title


class Scene(models.Model):
    story = models.ForeignKey(Story, related_name="scenes", on_delete=models.CASCADE)
    scene_content = models.TextField()
    background_image = models.URLField(blank=True, null=True)
    trust_level = models.IntegerField(default=0)
    is_ending = models.BooleanField(default=False)
    is_starting = models.BooleanField(default=False)
    

class Choice(models.Model):
    label = models.CharField(max_length=200)
    trust_level_change = models.IntegerField(default=0)
    scene = models.ForeignKey(Scene, related_name="choices", on_delete=models.CASCADE)

class PlayerState(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    current_scene = models.ForeignKey(Scene, on_delete=models.SET_NULL, null=True)
