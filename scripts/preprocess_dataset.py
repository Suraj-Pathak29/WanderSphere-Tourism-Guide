"""
1.  Validates and cleans the CSV (handles nulls, type coercions, encoding).
2.  Generates synthetic user-rating rows so the collaborative filter has
    enough data to work with on first run.
3.  Builds and saves the TF-IDF content matrix to recommendation_data/.
"""

import os
import sys
import argparse
import django
import logging
import json
import random
import numpy as np
import pandas as pd

# ── Bootstrap Django 
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tourism_guide.settings')
django.setup()

from destinations.models import Destination
from recommendations.engine import build_content_matrix, build_collab_matrix
from ratings.models import Rating
from accounts.models import CustomUser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger(__name__)

# ── Load & validate CSV 

def load_csv(csv_path: str) -> pd.DataFrame:
    log.info("Loading CSV: %s", csv_path)
    df = pd.read_csv(csv_path, encoding='utf-8')

    required_cols = {
        'id', 'city', 'country', 'region', 'short_description',
        'latitude', 'longitude', 'avg_temp_monthly', 'ideal_durations',
        'budget_level', 'culture', 'adventure', 'nature', 'beaches',
        'nightlife', 'cuisine', 'wellness', 'urban', 'seclusion',
    }
    missing = required_cols - set(df.columns)
    if missing:
        log.error("CSV is missing columns: %s", missing)
        sys.exit(1)

    log.info("Raw shape: %d rows × %d cols", *df.shape)
    return df

def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    log.info("Cleaning data …")

    # Drop rows missing critical fields
    df = df.dropna(subset=['city', 'country', 'latitude', 'longitude'])

    # Normalise budget_level
    valid_budgets = {'Budget', 'Mid-range', 'Luxury'}
    df['budget_level'] = df['budget_level'].str.strip().str.title()
    df.loc[~df['budget_level'].isin(valid_budgets), 'budget_level'] = 'Mid-range'

    # Normalise region
    df['region'] = df['region'].str.strip().str.lower()

    # Clamp feature scores 1–5
    score_cols = ['culture', 'adventure', 'nature', 'beaches',
                  'nightlife', 'cuisine', 'wellness', 'urban', 'seclusion']
    for col in score_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(3).clip(1, 5).astype(int)

    # Ensure numeric coords
    df['latitude']  = pd.to_numeric(df['latitude'],  errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df = df.dropna(subset=['latitude', 'longitude'])

    # Fill text fields
    df['short_description'] = df['short_description'].fillna('A beautiful destination.')
    df['avg_temp_monthly']  = df['avg_temp_monthly'].fillna('{}')
    df['ideal_durations']   = df['ideal_durations'].fillna('["One week"]')
    df['id']                = df['id'].fillna('').astype(str)

    log.info("Clean shape: %d rows", len(df))
    return df

# ── Upsert destinations into DB 

def import_destinations(df: pd.DataFrame) -> int:
    log.info("Importing destinations into database …")
    created_count = 0
    updated_count = 0

    for _, row in df.iterrows():
        obj, created = Destination.objects.update_or_create(
            external_id=str(row['id']),
            defaults={
                'city':              str(row['city']).strip(),
                'country':           str(row['country']).strip(),
                'region':            str(row['region']).strip(),
                'short_description': str(row['short_description']).strip(),
                'latitude':          float(row['latitude']),
                'longitude':         float(row['longitude']),
                'avg_temp_monthly':  str(row['avg_temp_monthly']),
                'ideal_durations':   str(row['ideal_durations']),
                'budget_level':      str(row['budget_level']),
                'culture':           int(row['culture']),
                'adventure':         int(row['adventure']),
                'nature':            int(row['nature']),
                'beaches':           int(row['beaches']),
                'nightlife':         int(row['nightlife']),
                'cuisine':           int(row['cuisine']),
                'wellness':          int(row['wellness']),
                'urban':             int(row['urban']),
                'seclusion':         int(row['seclusion']),
            },
        )
        if created:
            created_count += 1
        else:
            updated_count += 1

    log.info("Done: %d created, %d updated.", created_count, updated_count)
    return created_count + updated_count

# ── Seed synthetic ratings (for cold-start collab filter) 

def seed_synthetic_ratings(n_users: int = 30, ratings_per_user: int = 15):
    """
    Creates demo user accounts and random ratings so SVD has enough data.
    Skipped automatically if sufficient real ratings already exist.
    """
    real_count = Rating.objects.count()
    if real_count >= 100:
        log.info("Sufficient real ratings (%d). Skipping synthetic seed.", real_count)
        return

    log.info("Seeding %d synthetic users with %d ratings each …", n_users, ratings_per_user)
    dest_pks = list(Destination.objects.values_list('pk', flat=True))
    if not dest_pks:
        log.warning("No destinations in DB – run import first.")
        return

    random.seed(42)
    np.random.seed(42)

    for i in range(1, n_users + 1):
        username = f'demo_user_{i:03d}'
        user, created = CustomUser.objects.get_or_create(
            username=username,
            defaults={
                'email':            f'{username}@demo.local',
                'preferred_budget': random.choice(['Budget', 'Mid-range', 'Luxury']),
                'pref_culture':     random.randint(1, 5),
                'pref_adventure':   random.randint(1, 5),
                'pref_nature':      random.randint(1, 5),
                'pref_beaches':     random.randint(1, 5),
                'pref_nightlife':   random.randint(1, 5),
                'pref_cuisine':     random.randint(1, 5),
                'pref_wellness':    random.randint(1, 5),
                'pref_urban':       random.randint(1, 5),
                'pref_seclusion':   random.randint(1, 5),
            }
        )
        if created:
            user.set_unusable_password()
            user.save()

        # Pick a random sample of destinations to rate
        sample_pks = random.sample(dest_pks, min(ratings_per_user, len(dest_pks)))
        for pk in sample_pks:
            # Bias score toward user preference alignment
            dest = Destination.objects.get(pk=pk)
            pref = user.get_preference_vector()
            feat = dest.get_feature_vector()
            alignment = np.dot(pref, feat) / (np.linalg.norm(pref) * np.linalg.norm(feat) + 1e-9)
            # Map cosine similarity [0,1] to score [1,5] with noise
            raw_score = alignment * 4 + 1 + np.random.normal(0, 0.5)
            score = int(np.clip(round(raw_score), 1, 5))
            Rating.objects.get_or_create(
                user=user, destination_id=pk,
                defaults={'score': score}
            )

    log.info("Synthetic ratings seeded: %d total.", Rating.objects.count())

# ── Build recommendation matrices 

def build_matrices():
    log.info("Building content-based TF-IDF + feature matrices …")
    ids = build_content_matrix(Destination.objects.all())
    log.info("Content matrix: %d destinations indexed.", len(ids))

    log.info("Building collaborative filter (SVD) …")
    build_collab_matrix(Rating.objects.all(), n_components=20)
    log.info("All matrices saved to recommendation_data/")

# ── Main 

def main():
    parser = argparse.ArgumentParser(
        description='Preprocess the Kaggle travel CSV and initialise the Tourism Guide DB.'
    )
    parser.add_argument(
        '--csv', required=True,
        help='Path to the destinations_.csv file'
    )
    parser.add_argument(
        '--skip-seed', action='store_true',
        help='Skip synthetic rating generation'
    )
    args = parser.parse_args()

    if not os.path.isfile(args.csv):
        log.error("File not found: %s", args.csv)
        sys.exit(1)

    # 1. Load & clean
    df = load_csv(args.csv)
    df = clean_df(df)

    # 2. Import to DB
    total = import_destinations(df)
    log.info("Total destinations in DB: %d", Destination.objects.count())

    # 3. Seed synthetic ratings
    if not args.skip_seed:
        seed_synthetic_ratings()

    # 4. Build ML matrices
    build_matrices()

    log.info("=" * 60)
    log.info("✅  Preprocessing complete!")
    log.info("    Destinations : %d", Destination.objects.count())
    log.info("    Ratings      : %d", Rating.objects.count())
    log.info("    Run server   : python manage.py runserver")
    log.info("=" * 60)

if __name__ == '__main__':
    main()