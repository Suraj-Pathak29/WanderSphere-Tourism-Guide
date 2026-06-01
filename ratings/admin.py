from django.contrib import admin
from .models import Rating

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display  = ['user', 'destination', 'score', 'created_at']
    list_filter   = ['score']
    search_fields = ['user__username', 'destination__city']