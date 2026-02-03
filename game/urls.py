from django.urls import path, include
from .views import StoryView, SceneView, ChoiceView, PlayerStateView , SceneListView

urlpatterns = [
    path('stories/', StoryView.as_view(), name='story-list'),
    path('scenes/', SceneListView.as_view(), name='scene-detail'),
    path('scenes/<int:scene_id>/', SceneView.as_view(), name='scene-detail'),
    path('scenes/<int:scene_id>/choices/', ChoiceView.as_view(), name='choice-list'),

    path('choices/<int:choice_id>/select/', ChoiceView.as_view(), name='process-choice'),
    path('player-state/', PlayerStateView.as_view(), name='player-state'),

]
