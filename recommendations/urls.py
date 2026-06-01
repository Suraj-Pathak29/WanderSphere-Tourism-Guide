from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/',          views.dashboard,             name='dashboard'),
    path('similar/<int:pk>/',   views.similar_destinations,  name='similar_destinations'),
]
