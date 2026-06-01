from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .engine import hybrid_recommend, fallback_popular, content_scores_for_destination
from destinations.models import Destination
from ratings.models import Rating
from django.db.models import Avg

@login_required
def dashboard(request):
    """
    Hybrid recommendation dashboard:
    - "Places you might like"  → content-based top picks
    - "Users also visited"     → collaborative filter picks
    - Blended top-10 (hybrid)  → shown prominently
    """
    hybrid_results = hybrid_recommend(request.user, top_n=10, alpha=0.6)

    # Pure content picks (labelled separately in UI)
    from .engine import content_scores_for_user
    content_raw = content_scores_for_user(request.user.get_preference_vector(), top_n=6)
    content_pks = [pk for pk, _ in content_raw]
    content_picks = list(Destination.objects.filter(pk__in=content_pks))

    # User's recent ratings
    recent_ratings = (
        Rating.objects.filter(user=request.user)
        .select_related('destination')
        .order_by('-created_at')[:5]
    )

    # Stats
    rated_count = Rating.objects.filter(user=request.user).count()

    return render(request, 'recommendations/dashboard.html', {
        'hybrid_results': hybrid_results,
        'content_picks': content_picks,
        'recent_ratings': recent_ratings,
        'rated_count': rated_count,
    })

def similar_destinations(request, pk):
    """AJAX-friendly view returning destinations similar to pk."""
    scores = content_scores_for_destination(pk, top_n=6)
    similar_pks = [p for p, _ in scores]
    destinations = list(Destination.objects.filter(pk__in=similar_pks))
    return render(request, 'recommendations/similar.html', {
        'destinations': destinations,
        'source_pk': pk,
    })