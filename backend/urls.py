from django.contrib import admin
from django.urls import path
from backend import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/start/', views.start_story, name='start_story'),
    path('api/choice/', views.process_choice, name='process_choice'),
]
