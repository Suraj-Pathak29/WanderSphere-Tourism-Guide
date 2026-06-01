from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Rating(models.Model):
    """
    User rating for a destination (1-5 stars).
    This is the primary input for the Collaborative Filtering model.
    Each user can only rate a destination once (unique_together).
    """
    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings'
    )
    destination = models.ForeignKey(
        'destinations.Destination', on_delete=models.CASCADE, related_name='rating'
    )
    score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review      = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'destination')
        ordering        = ['-created_at']

    def __str__(self):
        return f"{self.user.username} → {self.destination.city}: {self.score}★"