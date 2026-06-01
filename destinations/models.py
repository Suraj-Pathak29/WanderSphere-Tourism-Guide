from django.db import models
import json

class Destination(models.Model):
    """
    Mirrors the Kaggle travel dataset columns exactly.
    Feature scores (culture … seclusion) are integers 1-5
    used directly by the recommendation engine.
    """

    BUDGET_CHOICES = [
        ('Budget', 'Budget'),
        ('Mid-range', 'Mid-range'),
        ('Luxury', 'Luxury'),
    ]

    REGION_CHOICES = [
        ('europe', 'Europe'),
        ('asia', 'Asia'),
        ('north_america', 'North America'),
        ('south_america', 'South America'),
        ('africa', 'Africa'),
        ('oceania', 'Oceania'),
        ('middle_east', 'Middle East'),
    ]

    # Identifiers
    external_id       = models.CharField(max_length=100, unique=True, blank=True)
    city              = models.CharField(max_length=100)
    country           = models.CharField(max_length=100)
    region            = models.CharField(max_length=50, choices=REGION_CHOICES, default='asia')
    short_description = models.TextField()

    # Geography
    latitude          = models.FloatField()
    longitude         = models.FloatField()

    # Climate — stored as raw JSON string from the CSV
    avg_temp_monthly  = models.TextField(blank=True)   # JSON: {"1": {"avg":..}, ..}
    ideal_durations   = models.TextField(blank=True)   # JSON array

    # Cost & Category
    budget_level      = models.CharField(max_length=20, choices=BUDGET_CHOICES, default='Mid-range')

    # Feature scores (1–5)
    culture           = models.IntegerField(default=3)
    adventure         = models.IntegerField(default=3)
    nature            = models.IntegerField(default=3)
    beaches           = models.IntegerField(default=3)
    nightlife         = models.IntegerField(default=3)
    cuisine           = models.IntegerField(default=3)
    wellness          = models.IntegerField(default=3)
    urban             = models.IntegerField(default=3)
    seclusion         = models.IntegerField(default=3)

    # Meta
    image_url         = models.URLField(blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['city']

    def __str__(self):
        return f"{self.city}, {self.country}"

    def get_feature_vector(self):
        """Return numeric feature scores as a list (same order as user prefs)."""
        return [
            self.culture, self.adventure, self.nature, self.beaches,
            self.nightlife, self.cuisine, self.wellness, self.urban, self.seclusion,
        ]

    def get_temp_data(self):
        """Parse avg_temp_monthly JSON for template use."""
        try:
            return json.loads(self.avg_temp_monthly)
        except (json.JSONDecodeError, TypeError):
            return {}

    def get_ideal_durations(self):
        """Parse ideal_durations JSON array."""
        try:
            return json.loads(self.ideal_durations)
        except (json.JSONDecodeError, TypeError):
            return []

    def get_best_months(self):
        """Return the 3 months with highest average temperature."""
        temp_data = self.get_temp_data()
        if not temp_data:
            return []
        month_names = {
            '1': 'Jan', '2': 'Feb', '3': 'Mar', '4': 'Apr',
            '5': 'May', '6': 'Jun', '7': 'Jul', '8': 'Aug',
            '9': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec',
        }
        sorted_months = sorted(
            temp_data.items(),
            key=lambda x: x[1].get('avg', 0),
            reverse=True,
        )
        return [month_names.get(m, m) for m, _ in sorted_months[:3]]

    def safety_status(self):
        """
        Simple rule-based flag:
        Destinations in extreme-heat months (avg > 38°C) or freezing months (<0°C)
        are flagged 'Risky'; otherwise 'Safe'.
        """
        import datetime
        current_month = str(datetime.date.today().month)
        temp_data = self.get_temp_data()
        if not temp_data or current_month not in temp_data:
            return 'Unknown'
        avg = temp_data[current_month].get('avg', 20)
        if avg > 38 or avg < 0:
            return 'Risky'
        return 'Safe'


class Utility(models.Model):
    """Local utilities (ATMs, Washrooms, Hospitals) shown in the Leaflet map."""
    UTILITY_TYPES = [
        ('ATM', 'ATM'),
        ('Washroom', 'Washroom'),
        ('Hospital', 'Hospital'),
        ('Police', 'Police'),
        ('Hotel', 'Hotel'),
    ]
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='utilities')
    name        = models.CharField(max_length=200)
    utility_type = models.CharField(max_length=20, choices=UTILITY_TYPES)
    latitude    = models.FloatField()
    longitude   = models.FloatField()
    address     = models.TextField(blank=True)

    def __str__(self):
        return f"{self.utility_type} – {self.name}"
