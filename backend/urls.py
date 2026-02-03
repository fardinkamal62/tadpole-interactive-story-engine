from django.contrib import admin
from django.urls import path
from backend import settings, views
from django.conf import settings   # 🔥 এটা তোমার missing ছিল
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/start/', views.start_story, name='start_story'),
    path('api/choice/', views.process_choice, name='process_choice'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)