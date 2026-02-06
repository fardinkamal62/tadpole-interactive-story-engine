from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Story, Scene, Choice, PlayerState
from .serializers import StorySerializer, SceneSerializer, ChoiceSerializer, PlayerStateSerializer


class StoryView(APIView):
    def get(self, request):
        stories = Story.objects.all()
        serializer = StorySerializer(stories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class SceneListView(APIView):
    def get(self, request):
        scenes = Scene.objects.all()
        serializer = SceneSerializer(scenes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SceneView(APIView):
    def get(self, request, scene_id):
        try:
            scene = Scene.objects.get(id=scene_id)
        except Scene.DoesNotExist:
            return Response({"error": "Scene not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = SceneSerializer(scene)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class ChoiceView(APIView):
    def get(self, request, scene_id):
        try:
            scene = Scene.objects.get(id=scene_id)
        except Scene.DoesNotExist:
            return Response({"error": "Scene not found"}, status=status.HTTP_404_NOT_FOUND)

        choices = scene.choices.all()
        serializer = ChoiceSerializer(choices, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request, choice_id):
        user = 1
        try:
            choice = self.new_method(choice_id)
        except Choice.DoesNotExist:
            return Response({"error": "Choice not found"}, status=status.HTTP_404_NOT_FOUND)
        
        scene = choice.scene
        story = scene.story


        
        

        player_serializer = PlayerStateSerializer(data={
            "user": user,
            "story": story.id,
            "current_scene": scene.id
        })
        if player_serializer.is_valid():
            player_serializer.save()
        else:
            return Response(player_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

        new_trust_level = scene.trust_level + choice.trust_level_change

        if new_trust_level < 0 and scene.is_starting:
            new_trust_level = 0 + choice.trust_level_change

        print("New Trust Level:", new_trust_level)

        get_scene = Scene.objects.filter(trust_level=new_trust_level).first()
        
        if not get_scene:
            return Response({"error": "No scene found for this trust level"}, status=status.HTTP_404_NOT_FOUND)
        serializer = SceneSerializer(get_scene)

        if get_scene.is_ending:
            return Response({"message": "You've reached an ending!", "scene": serializer.data}, status=status.HTTP_200_OK)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def new_method(self, choice_id):
        choice = Choice.objects.get(id=choice_id)
        return choice
    

class PlayerStateView(APIView):
    def get(self, request):
        user = 1
        player_states = PlayerState.objects.filter(user=user)
        serializer = PlayerStateSerializer(player_states, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

