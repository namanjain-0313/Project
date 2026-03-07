# backend/pipeline/resolution.py
# Entity Resolution: maps raw entity names to canonical Wikidata IDs
# So "PM Modi", "Narendra Modi", "Modi ji" all become Q1058580

import logging
import numpy as np
from rapidfuzz import fuzz
from .constants import CANONICAL_ENTITIES

logger = logging.getLogger(__name__)

# Load sentence transformer model once
_embed_model = None

def get_embed_model():
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        _embed_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Loaded sentence-transformers model")
    return _embed_model


def build_alias_index() -> dict[str, str]:
    """
    Build a flat lookup: alias → canonical name
    Used for fast exact/fuzzy matching before doing expensive embedding comparison.

    Example output:
    {
        "modi": "Narendra Modi",
        "pm modi": "Narendra Modi",
        "xi": "Xi Jinping",
        "beijing": "China",
        ...
    }
    """
    alias_index = {}
    for canonical_name, data in CANONICAL_ENTITIES.items():
        # Add the canonical name itself
        alias_index[canonical_name.lower()] = canonical_name
        # Add all aliases
        for alias in data.get('aliases', []):
            alias_index[alias.lower()] = canonical_name
    return alias_index


# Build once at module level
_alias_index = build_alias_index()


def resolve_entity(raw_name: str) -> dict:
    """
    Takes a raw entity mention (e.g., "PM Modi") and returns:
    - canonical_name: the standard name (e.g., "Narendra Modi")
    - wikidata_id: the Wikidata ID (e.g., "Q1058580")
    - type: PERSON / COUNTRY / ORGANIZATION / LOCATION
    - confidence: how confident we are in the match

    Strategy (in order of speed/cost):
    1. Exact alias match — instant, free
    2. Fuzzy string match — fast, cheap
    3. Embedding similarity — slower, most accurate for ambiguous cases
    """
    if not raw_name or len(raw_name.strip()) < 2:
        return _unknown_entity(raw_name)

    normalized = raw_name.strip().lower()

    # ── Step 1: Exact alias match ─────────────────────────
    if normalized in _alias_index:
        canonical = _alias_index[normalized]
        entity_data = CANONICAL_ENTITIES[canonical]
        return {
            'raw_name': raw_name,
            'canonical_name': canonical,
            'wikidata_id': entity_data['wikidata_id'],
            'type': entity_data['type'],
            'confidence': 1.0,
            'method': 'exact'
        }

    # ── Step 2: Fuzzy string match ────────────────────────
    best_fuzzy_score = 0
    best_fuzzy_canonical = None

    for alias, canonical in _alias_index.items():
        score = fuzz.ratio(normalized, alias) / 100.0
        if score > best_fuzzy_score:
            best_fuzzy_score = score
            best_fuzzy_canonical = canonical

    if best_fuzzy_score > 0.85:
        entity_data = CANONICAL_ENTITIES[best_fuzzy_canonical]
        return {
            'raw_name': raw_name,
            'canonical_name': best_fuzzy_canonical,
            'wikidata_id': entity_data['wikidata_id'],
            'type': entity_data['type'],
            'confidence': best_fuzzy_score,
            'method': 'fuzzy'
        }

    # ── Step 3: Embedding similarity ─────────────────────
    # Only run this for things that are somewhat close (avoids noise)
    if best_fuzzy_score > 0.5:
        model = get_embed_model()
        canonical_names = list(CANONICAL_ENTITIES.keys())

        raw_embedding = model.encode([raw_name])
        canonical_embeddings = model.encode(canonical_names)

        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(raw_embedding, canonical_embeddings)[0]

        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])

        if best_score > 0.75:
            canonical = canonical_names[best_idx]
            entity_data = CANONICAL_ENTITIES[canonical]
            return {
                'raw_name': raw_name,
                'canonical_name': canonical,
                'wikidata_id': entity_data['wikidata_id'],
                'type': entity_data['type'],
                'confidence': best_score,
                'method': 'embedding'
            }

    # ── No match found ────────────────────────────────────
    return _unknown_entity(raw_name)


def _unknown_entity(raw_name: str) -> dict:
    """Return a placeholder for entities we can't resolve"""
    return {
        'raw_name': raw_name,
        'canonical_name': raw_name,
        'wikidata_id': None,
        'type': 'UNKNOWN',
        'confidence': 0.0,
        'method': 'none'
    }


def resolve_triples(triples: list[dict]) -> list[dict]:
    """
    Run entity resolution on all subjects and objects in a list of triples.
    Adds resolved entity data to each triple.
    """
    resolved = []
    for triple in triples:
        subject_resolved = resolve_entity(triple['subject'])
        object_resolved  = resolve_entity(triple['object'])

        resolved.append({
            **triple,
            'subject_resolved': subject_resolved,
            'object_resolved': object_resolved
        })

    return resolved