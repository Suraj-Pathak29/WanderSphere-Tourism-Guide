from django.contrib import admin
from .models import Destination, Utility

class UtilityInline(admin.TabularInline):
    model = Utility
    extra = 1

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display  = ['city', 'country', 'region', 'budget_level', 'safety_status']
    list_filter   = ['region', 'budget_level']
    search_fields = ['city', 'country']
    inlines       = [UtilityInline]

@admin.register(Utility)
class UtilityAdmin(admin.ModelAdmin):
    list_display = ['name', 'utility_type', 'destination']
