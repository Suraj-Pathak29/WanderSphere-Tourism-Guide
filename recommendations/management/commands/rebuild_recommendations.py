"""
Management command to rebuild recommendation matrices.

Usage:
    python manage.py rebuild_recommendations
    python manage.py rebuild_recommendations --collab-only
    python manage.py rebuild_recommendations --content-only
"""

from django.core.management.base import BaseCommand
from recommendations.engine import build_content_matrix, build_collab_matrix
from destinations.models import Destination
from ratings.models import Rating


class Command(BaseCommand):
    help = 'Rebuild the hybrid recommendation engine matrices (TF-IDF + SVD).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--content-only', action='store_true',
            help='Only rebuild the content-based TF-IDF matrix.'
        )
        parser.add_argument(
            '--collab-only', action='store_true',
            help='Only rebuild the collaborative filter SVD matrix.'
        )
        parser.add_argument(
            '--n-components', type=int, default=20,
            help='Number of SVD components (default: 20).'
        )

    def handle(self, *args, **options):
        content_only = options['content_only']
        collab_only  = options['collab_only']

        if not collab_only:
            self.stdout.write('Building content-based matrices…')
            n = Destination.objects.count()
            if n == 0:
                self.stderr.write('⚠  No destinations in DB. Run the preprocessing script first.')
                return
            ids = build_content_matrix(Destination.objects.all())
            self.stdout.write(self.style.SUCCESS(f'✅  Content matrix built for {len(ids)} destinations.'))

        if not content_only:
            self.stdout.write('Building collaborative filter (SVD)…')
            n = Rating.objects.count()
            if n < 5:
                self.stderr.write(f'⚠  Only {n} rating(s) found. Need at least 5 for SVD. '
                                  'Run preprocessing script to seed synthetic data.')
            else:
                build_collab_matrix(Rating.objects.all(), n_components=options['n_components'])
                self.stdout.write(self.style.SUCCESS(f'✅  SVD matrix built from {n} ratings.'))

        self.stdout.write(self.style.SUCCESS('Done. Recommendation engine is up to date.'))
