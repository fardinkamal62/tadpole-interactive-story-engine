from django.contrib import admin
from .models import Story, Scene, Choice, PlayerState

admin.site.register(Story)
admin.site.register(Scene)
admin.site.register(Choice)
admin.site.register(PlayerState)
