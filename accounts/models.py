from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    """
    Extended user model that stores travel preferences
    used to bootstrap the content-based recommendation engine.
    """
    BUDGET_CHOICES = [
        ('Budget', 'Budget'),
        ('Mid-range', 'Mid-range'),
        ('Luxury', 'Luxury'),
    ]

    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    preferred_budget = models.CharField(
        max_length=20, choices=BUDGET_CHOICES, default='Mid-range'
    )

    # Interest scores (1–5) mirror the destination feature columns
    pref_culture    = models.IntegerField(default=3)
    pref_adventure  = models.IntegerField(default=3)
    pref_nature     = models.IntegerField(default=3)
    pref_beaches    = models.IntegerField(default=3)
    pref_nightlife  = models.IntegerField(default=3)
    pref_cuisine    = models.IntegerField(default=3)
    pref_wellness   = models.IntegerField(default=3)
    pref_urban      = models.IntegerField(default=3)
    pref_seclusion  = models.IntegerField(default=3)

    def __str__(self):
        return self.username

    def get_preference_vector(self):
        """Return user preferences as a list for cosine similarity computation."""
        return [
            self.pref_culture, self.pref_adventure, self.pref_nature,
            self.pref_beaches, self.pref_nightlife, self.pref_cuisine,
            self.pref_wellness, self.pref_urban, self.pref_seclusion,
        ]
