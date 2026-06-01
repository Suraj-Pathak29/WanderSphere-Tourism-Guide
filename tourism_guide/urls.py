"""tourism_guide URL Configuration"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from destinations import views as dest_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dest_views.home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('destinations/', include('destinations.urls')),
    path('recommendations/', include('recommendations.urls')),
    path('ratings/', include('ratings.urls')),
    path('safety/', include('safety.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
