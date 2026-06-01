from django.contrib import admin
from .models import SafetyAlert

@admin.register(SafetyAlert)
class SafetyAlertAdmin(admin.ModelAdmin):
    list_display  = ['destination', 'title', 'severity', 'valid_from', 'valid_until', 'is_active']
    list_filter   = ['severity', 'is_active']
    search_fields = ['destination__city', 'title']
