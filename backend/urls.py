from django.contrib import admin
from django.urls import path, include
from backend.views import home_page, login_page, start_story, process_choice

urlpatterns = [
    path('admin/', admin.site.urls),

    # Frontend views
    path('', home_page, name='home_page'),
    path('login/', login_page, name='login_page'),

    path('api/start/', start_story, name='start_story'),
    path('api/choice/', process_choice, name='process_choice'),
    path('api/auth/', include('apps.authentication.urls')),
]
