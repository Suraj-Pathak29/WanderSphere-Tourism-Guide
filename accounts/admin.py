from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display  = ['username', 'email', 'preferred_budget', 'is_staff']
    fieldsets     = UserAdmin.fieldsets + (
        ('Travel Preferences', {
            'fields': (
                'preferred_budget', 'bio', 'avatar',
                'pref_culture', 'pref_adventure', 'pref_nature', 'pref_beaches',
                'pref_nightlife', 'pref_cuisine', 'pref_wellness', 'pref_urban', 'pref_seclusion',
            )
        }),
    )
