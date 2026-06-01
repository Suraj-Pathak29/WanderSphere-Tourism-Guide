from django.urls import path
from . import views

urlpatterns = [
    path('',           views.safety_overview,    name='safety_overview'),
    path('<int:pk>/',  views.destination_safety, name='destination_safety'),
]