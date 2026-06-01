from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
import json
from .models import Rating
from destinations.models import Destination

@login_required
@require_POST
def rate_destination(request, pk):
    """
    Create or update a rating via AJAX (JSON body) or form POST.
    After saving, triggers a background rebuild of the collab matrix.
    """
    destination = get_object_or_404(Destination, pk=pk)

    if request.content_type == 'application/json':
        data  = json.loads(request.body)
        score = int(data.get('score', 0))
        review = data.get('review', '')
    else:
        score  = int(request.POST.get('score', 0))
        review = request.POST.get('review', '')

    if not (1 <= score <= 5):
        if request.content_type == 'application/json':
            return JsonResponse({'error': 'Score must be 1–5'}, status=400)
        messages.error(request, 'Invalid rating score.')
        return redirect('destination_detail', pk=pk)

    rating, created = Rating.objects.update_or_create(
        user=request.user,
        destination=destination,
        defaults={'score': score, 'review': review},
    )
    _trigger_collab_rebuild()

    if request.content_type == 'application/json':
        return JsonResponse({
            'status': 'created' if created else 'updated',
            'score': rating.score,
            'destination': destination.city,
        })

    action = 'submitted' if created else 'updated'
    messages.success(request, f'Your rating has been {action}!')
    return redirect('destination_detail', pk=pk)

@login_required
def my_ratings(request):
    from django.shortcuts import render
    ratings = (
        Rating.objects
        .filter(user=request.user)
        .select_related('destination')
        .order_by('-created_at')
    )
    return render(request, 'ratings/my_ratings.html', {'ratings': ratings})

def _trigger_collab_rebuild():
    """
    Rebuild the collaborative filter in a background thread so the main
    request is not blocked.  Errors are logged but never raised.
    """
    import threading
    import logging
    logger = logging.getLogger(__name__)

    def _rebuild():
        try:
            from ratings.models import Rating as R
            from recommendations.engine import build_collab_matrix
            build_collab_matrix(R.objects.all())
            logger.info("Collaborative filter rebuilt after new rating.")
        except Exception as exc:
            logger.exception("Background collab rebuild failed: %s", exc)

    t = threading.Thread(target=_rebuild, daemon=True)
    t.start()