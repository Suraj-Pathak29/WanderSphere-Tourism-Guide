import json
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Avg, Q
from .models import Destination, Utility
from ratings.models import Rating

def home(request):
    """Landing page with featured destinations."""
    featured = Destination.objects.order_by('?')[:6]
    total    = Destination.objects.count()
    return render(request, 'destinations/home.html', {
        'featured': featured,
        'total': total,
    })

def destination_list(request):
    """Browsable, filterable destination catalogue."""
    qs = Destination.objects.all()

    # Filters from GET params
    region       = request.GET.get('region', '')
    budget       = request.GET.get('budget', '')
    search_query = request.GET.get('q', '')

    if region:
        qs = qs.filter(region=region)
    if budget:
        qs = qs.filter(budget_level=budget)
    if search_query:
        qs = qs.filter(
            Q(city__icontains=search_query) |
            Q(country__icontains=search_query) |
            Q(short_description__icontains=search_query)
        )

    paginator = Paginator(qs, 12)
    page_obj  = paginator.get_page(request.GET.get('page'))

    regions = Destination.objects.values_list('region', flat=True).distinct()
    return render(request, 'destinations/list.html', {
        'page_obj': page_obj,
        'regions': regions,
        'selected_region': region,
        'selected_budget': budget,
        'search_query': search_query,
    })

def destination_detail(request, pk):
    """Full detail page for a single destination."""
    destination = get_object_or_404(Destination, pk=pk)
    utilities   = destination.utilities.all()
    ratings     = Rating.objects.filter(destination=destination)
    avg_rating  = ratings.aggregate(avg=Avg('score'))['avg'] or 0
    user_rating = None
    if request.user.is_authenticated:
        user_rating = ratings.filter(user=request.user).first()

    # Prepare climate chart data
    temp_data = destination.get_temp_data()
    months    = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    avg_temps = [temp_data.get(str(i+1), {}).get('avg', 0) for i in range(12)]

    # Utilities JSON for Leaflet
    utils_json = json.dumps([
        {
            'name': u.name,
            'type': u.utility_type,
            'lat': u.latitude,
            'lng': u.longitude,
            'address': u.address,
        }
        for u in utilities
    ])

    dest_scores = [
        ('Culture',   destination.culture),
        ('Adventure', destination.adventure),
        ('Nature',    destination.nature),
        ('Beaches',   destination.beaches),
        ('Nightlife', destination.nightlife),
        ('Cuisine',   destination.cuisine),
        ('Wellness',  destination.wellness),
        ('Urban',     destination.urban),
        ('Seclusion', destination.seclusion),
    ]

    return render(request, 'destinations/detail.html', {
        'destination': destination,
        'avg_rating': round(avg_rating, 1),
        'user_rating': user_rating,
        'rating_count': ratings.count(),
        'months': json.dumps(months),
        'avg_temps': json.dumps(avg_temps),
        'utils_json': utils_json,
        'best_months': destination.get_best_months(),
        'ideal_durations': destination.get_ideal_durations(),
        'safety_status': destination.safety_status(),
        'dest_scores': dest_scores,
    })

def map_view(request):
    """Full-screen Leaflet.js map with all destination markers."""
    destinations = Destination.objects.all().values(
        'id', 'city', 'country', 'latitude', 'longitude',
        'budget_level', 'short_description',
    )
    destinations_json = json.dumps(list(destinations))
    return render(request, 'destinations/map.html', {
        'destinations_json': destinations_json,
    })