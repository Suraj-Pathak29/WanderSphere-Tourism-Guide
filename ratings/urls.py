from django.urls import path
from . import views

urlpatterns = [
    path('rate/<int:pk>/',  views.rate_destination, name='rate_destination'),
    path('my-ratings/',     views.my_ratings,       name='my_ratings'),
]
