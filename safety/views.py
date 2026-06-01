import datetime
from django.shortcuts import render, get_object_or_404
from destinations.models import Destination
from .models import SafetyAlert

def safety_overview(request):
    """
    Safety & Utility Guide:
    Classifies all destinations as Safe / Risky / Unknown for the current month.
    Also surfaces any active admin-posted SafetyAlerts.
    """
    today   = datetime.date.today()
    all_dest = Destination.objects.prefetch_related('safety_alerts').all()

    safe_list  = []
    risky_list = []

    for d in all_dest:
        status = d.safety_status()

        # Upgrade to Risky if there's an active admin alert
        active_alerts = d.safety_alerts.filter(
            is_active=True,
            valid_from__lte=today,
            valid_until__gte=today,
        )
        if active_alerts.exists():
            status = 'Risky'

        if status == 'Risky':
            risky_list.append((d, list(active_alerts)))
        else:
            safe_list.append(d)

    return render(request, 'safety/overview.html', {
        'safe_list':  safe_list,
        'risky_list': risky_list,
        'current_month': today.strftime('%B'),
    })

def destination_safety(request, pk):
    """Detail safety page for a single destination."""
    destination = get_object_or_404(Destination, pk=pk)
    today       = datetime.date.today()
    alerts      = destination.safety_alerts.filter(
        is_active=True,
        valid_from__lte=today,
        valid_until__gte=today,
    )
    temp_data   = destination.get_temp_data()
    current_temp = temp_data.get(str(today.month), {})

    return render(request, 'safety/detail.html', {
        'destination':    destination,
        'alerts':         alerts,
        'safety_status':  destination.safety_status(),
        'current_temp':   current_temp,
        'current_month':  today.strftime('%B'),
    })