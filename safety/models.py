from django.db import models
from destinations.models import Destination

class SafetyAlert(models.Model):
    """
    Manual safety alerts that override the automatic temperature-based flag.
    Administrators can add alerts for civil unrest, natural disasters, etc.
    """
    SEVERITY_CHOICES = [
        ('Low',      'Low'),
        ('Moderate', 'Moderate'),
        ('High',     'High'),
        ('Critical', 'Critical'),
    ]

    destination = models.ForeignKey(
        Destination, on_delete=models.CASCADE, related_name='safety_alerts'
    )
    title       = models.CharField(max_length=200)
    description = models.TextField()
    severity    = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='Moderate')
    valid_from  = models.DateField()
    valid_until = models.DateField()
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.severity}] {self.destination.city} – {self.title}"
