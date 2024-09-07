from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', include("django_admin_kubi.urls")), 
    path('admin/', admin.site.urls),
    path('', include('members.urls')),  # Include URLs from the members app
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)