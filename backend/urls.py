from django.contrib import admin
from django.urls import path, include
from backend.views import (
    home_page,
    login_page,
    story_list_page,
    create_story_page,
    story_edit_page,
    story_scene_editor_page,
    story_play_page,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Frontend views
    path('', home_page, name='home_page'),
    path('login/', login_page, name='login_page'),

    path('api/auth/', include('apps.authentication.urls')),

    # Story routes
    path('story/', story_list_page, name='story_list_page'),
    path('story/create/', create_story_page, name='create_story_page'),
    path('story/<int:story_id>/edit/', story_edit_page, name='story_edit_page'),
    path('story/<int:story_id>/scenes/', story_scene_editor_page, name='story_scene_editor_page'),
    path('story/<int:story_id>/', story_play_page, name='story_play_page'),
    path('story/api/', include('apps.story.urls')),
]
