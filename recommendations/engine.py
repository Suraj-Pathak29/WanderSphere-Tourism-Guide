"""
Hybrid Recommendation Engine
Combines:
  1. Content-Based Filtering  - TF-IDF on text description + cosine similarity
                                 on numeric feature vectors (culture, adventure …)
  2. Collaborative Filtering  - SVD matrix factorisation on the user-destination
                                 ratings matrix (scipy sparse SVD).
"""

import os
import pickle
import numpy as np
import logging
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)

# Lazy-loaded globals (populated once per process) 
_content_matrix   = None   # shape (N_destinations, N_tfidf_features)
_feature_matrix   = None   # shape (N_destinations, 9)  — numeric scores
_dest_ids         = None   # list of Destination PKs, same order as rows
_user_item_matrix = None   # shape (N_users, N_destinations) — collab
_user_ids         = None   # list of user PKs
_collab_U         = None   # left singular vectors (users)
_collab_Vt        = None   # right singular vectors (destinations)
_collab_S         = None   # singular values

def _data_dir() -> Path:
    d = Path(settings.BASE_DIR) / 'recommendation_data'
    d.mkdir(exist_ok=True)
    return d

def _load_pickle(name):
    path = _data_dir() / f"{name}.pkl"
    if path.exists():
        with open(path, 'rb') as f:
            return pickle.load(f)
    return None

def _save_pickle(name, obj):
    path = _data_dir() / f"{name}.pkl"
    with open(path, 'wb') as f:
        pickle.dump(obj, f)

# BUILD (called by the preprocessing script) 

def build_content_matrix(destinations_qs):
    """
    Build TF-IDF matrix from destination descriptions and save to disk.
    Also saves a numeric feature matrix for direct cosine similarity.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import MinMaxScaler

    dest_list = list(destinations_qs.values(
        'id', 'short_description', 'country', 'region', 'budget_level',
        'culture', 'adventure', 'nature', 'beaches',
        'nightlife', 'cuisine', 'wellness', 'urban', 'seclusion',
    ))

    ids   = [d['id'] for d in dest_list]
    texts = [
        f"{d['short_description']} {d['country']} {d['region']} {d['budget_level']}"
        for d in dest_list
    ]

    # TF-IDF on text
    vectorizer = TfidfVectorizer(max_features=300, stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(texts).toarray()

    # Numeric feature matrix (culture … seclusion)
    feature_keys = ['culture','adventure','nature','beaches',
                    'nightlife','cuisine','wellness','urban','seclusion']
    feat_matrix = np.array([[d[k] for k in feature_keys] for d in dest_list], dtype=float)
    scaler = MinMaxScaler()
    feat_matrix_scaled = scaler.fit_transform(feat_matrix)

    _save_pickle('content_tfidf',  tfidf_matrix)
    _save_pickle('feature_matrix', feat_matrix_scaled)
    _save_pickle('dest_ids',       ids)
    _save_pickle('tfidf_vectorizer', vectorizer)
    logger.info("Content matrices built for %d destinations.", len(ids))
    return ids

def build_collab_matrix(ratings_qs, n_components=20):
    """
    Build user-item matrix, run truncated SVD, save decomposition to disk.
    ratings_qs: Rating queryset with .user_id, .destination_id, .score
    """
    from scipy.sparse import csr_matrix
    from scipy.sparse.linalg import svds

    ratings = list(ratings_qs.values('user_id', 'destination_id', 'score'))
    if not ratings:
        logger.warning("No ratings found — skipping collaborative filter build.")
        return

    user_ids  = sorted(set(r['user_id']  for r in ratings))
    dest_ids  = sorted(set(r['destination_id'] for r in ratings))
    u_idx     = {uid: i for i, uid in enumerate(user_ids)}
    d_idx     = {did: i for i, did in enumerate(dest_ids)}

    rows = [u_idx[r['user_id']]        for r in ratings]
    cols = [d_idx[r['destination_id']] for r in ratings]
    data = [float(r['score'])          for r in ratings]

    matrix = csr_matrix((data, (rows, cols)),
                         shape=(len(user_ids), len(dest_ids)))

    k = min(n_components, min(matrix.shape) - 1)
    U, S, Vt = svds(matrix.toarray(), k=k)

    _save_pickle('collab_U',        U)
    _save_pickle('collab_S',        S)
    _save_pickle('collab_Vt',       Vt)
    _save_pickle('collab_user_ids', user_ids)
    _save_pickle('collab_dest_ids', dest_ids)
    logger.info("Collaborative filter built: %d users × %d destinations, k=%d",
                len(user_ids), len(dest_ids), k)

# LOAD 

def _ensure_loaded():
    global _content_matrix, _feature_matrix, _dest_ids
    global _user_item_matrix, _user_ids
    global _collab_U, _collab_Vt, _collab_S

    if _dest_ids is None:
        _content_matrix = _load_pickle('content_tfidf')
        _feature_matrix = _load_pickle('feature_matrix')
        _dest_ids       = _load_pickle('dest_ids')
        _collab_U       = _load_pickle('collab_U')
        _collab_S       = _load_pickle('collab_S')
        _collab_Vt      = _load_pickle('collab_Vt')

# RECOMMEND 

def content_scores_for_user(user_preference_vector, top_n=20):
    """
    Given a 9-element user preference vector, compute cosine similarity
    against every destination's numeric feature vector.
    Returns list of (dest_pk, score) sorted descending.
    """
    _ensure_loaded()
    if _feature_matrix is None or _dest_ids is None:
        return []

    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.preprocessing import MinMaxScaler

    user_vec = np.array(user_preference_vector, dtype=float).reshape(1, -1)
    # Normalise to [0,1] range — same scaler range (1-5 → 0-1)
    user_vec = (user_vec - 1.0) / 4.0

    sims = cosine_similarity(user_vec, _feature_matrix)[0]
    ranked = sorted(zip(_dest_ids, sims.tolist()), key=lambda x: x[1], reverse=True)
    return ranked[:top_n]

def content_scores_for_destination(dest_pk, top_n=10):
    """
    Given a destination pk, return similar destinations using TF-IDF cosine sim.
    """
    _ensure_loaded()
    if _content_matrix is None or _dest_ids is None:
        return []

    from sklearn.metrics.pairwise import cosine_similarity

    if dest_pk not in _dest_ids:
        return []
    idx  = _dest_ids.index(dest_pk)
    vec  = _content_matrix[idx].reshape(1, -1)
    sims = cosine_similarity(vec, _content_matrix)[0]
    ranked = [
        (_dest_ids[i], sims[i])
        for i in np.argsort(sims)[::-1]
        if _dest_ids[i] != dest_pk
    ]
    return ranked[:top_n]

def collab_scores_for_user(user_pk, top_n=20):
    """
    Use the pre-computed SVD to predict scores for all destinations for a user.
    Returns list of (dest_pk, predicted_score) sorted descending.
    """
    _ensure_loaded()
    if _collab_U is None:
        return []

    collab_user_ids = _load_pickle('collab_user_ids')
    collab_dest_ids = _load_pickle('collab_dest_ids')

    if collab_user_ids is None or user_pk not in collab_user_ids:
        return []

    u_idx = collab_user_ids.index(user_pk)

    # Guard: if the matrix was built before this user was added,
    # their index will be out of bounds — fall back to content-only.
    if u_idx >= _collab_U.shape[0]:
        return []

    user_vec  = _collab_U[u_idx]
    predicted = user_vec @ np.diag(_collab_S) @ _collab_Vt
    # Normalise to [0, 1]
    mn, mx = predicted.min(), predicted.max()
    if mx > mn:
        predicted = (predicted - mn) / (mx - mn)

    ranked = sorted(
        zip(collab_dest_ids, predicted.tolist()),
        key=lambda x: x[1], reverse=True,
    )
    return ranked[:top_n]

def hybrid_recommend(user, top_n=10, alpha=0.6):
    """
    Main entry point.
    alpha  = weight for content-based score (1-alpha for collaborative).
    Returns list of (Destination, final_score) pairs.
    """
    from destinations.models import Destination
    from ratings.models import Rating

    pref_vec = user.get_preference_vector()
    content_raw  = content_scores_for_user(pref_vec, top_n=50)
    collab_raw   = collab_scores_for_user(user.pk, top_n=50)

    # Build score dicts
    content_dict = dict(content_raw)
    collab_dict  = dict(collab_raw)

    all_pks = set(content_dict.keys()) | set(collab_dict.keys())

    # Already-rated destinations (don't re-recommend)
    rated_pks = set(
        Rating.objects.filter(user=user).values_list('destination_id', flat=True)
    )

    combined = []
    for pk in all_pks:
        if pk in rated_pks:
            continue
        c_score = content_dict.get(pk, 0.0)
        f_score = collab_dict.get(pk, 0.0)
        score   = alpha * c_score + (1 - alpha) * f_score
        combined.append((pk, score))

    combined.sort(key=lambda x: x[1], reverse=True)
    top_pks   = [pk for pk, _ in combined[:top_n]]
    top_scores = {pk: sc for pk, sc in combined[:top_n]}

    destinations = {d.pk: d for d in Destination.objects.filter(pk__in=top_pks)}
    result = [
        (destinations[pk], round(top_scores[pk] * 100, 1))
        for pk in top_pks if pk in destinations
    ]
    return result

def fallback_popular(top_n=10):
    """
    Fallback for anonymous users — return top-rated destinations.
    """
    from django.db.models import Avg
    from destinations.models import Destination

    return (
        Destination.objects
        .annotate(avg_score=Avg('rating__score'))
        .order_by('-avg_score')[:top_n]
    )