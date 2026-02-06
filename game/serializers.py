from rest_framework.serializers import ModelSerializer

from .models import Story, Scene, Choice, PlayerState


class StorySerializer(ModelSerializer):
    class Meta:
        model = Story
        fields = '__all__'

class SceneSerializer(ModelSerializer):
    class Meta:
        model = Scene
        fields = '__all__'

class ChoiceSerializer(ModelSerializer):
    class Meta:
        model = Choice
        fields = '__all__'

class PlayerStateSerializer(ModelSerializer):
    class Meta:
        model = PlayerState
        fields = '__all__'
