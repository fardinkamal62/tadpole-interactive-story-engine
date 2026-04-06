from django.urls import path

from . import views

urlpatterns = [
    path("start/", views.start_story, name="start_story"),
    path("choice/", views.process_choice, name="process_choice"),
]

