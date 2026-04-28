from django.urls import path

from . import views

urlpatterns = [
    path("start/", views.start_story, name="start_story"),
    path("choice/", views.process_choice, name="process_choice"),
    path("create/", views.create_story, name="create_story"),
    path("<int:story_id>/update/", views.update_story, name="update_story"),
    path("<int:story_id>/scenes/", views.list_story_scenes, name="list_story_scenes"),
    path("<int:story_id>/scenes/create/", views.create_story_scene, name="create_story_scene"),
    path("<int:story_id>/scenes/<int:scene_id>/update/", views.update_story_scene, name="update_story_scene"),
    path("<int:story_id>/scenes/<int:scene_id>/delete/", views.delete_story_scene, name="delete_story_scene"),
]
