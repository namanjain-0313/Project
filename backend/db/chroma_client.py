# backend/db/chroma_client.py
# ChromaDB for semantic search — used by the RAG Q&A pipeline

import logging
import os
import chromadb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_chroma_client = None
_collection    = None
_embed_model   = None


def get_collection():
    global _chroma_client, _collection
    if _collection is None:
        _chroma_client = chromadb.Client()  # in-memory for prototype
        _collection = _chroma_client.get_or_create_collection(
            name="goe_events",
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("ChromaDB collection ready")
    return _collection


def get_embed_model():
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Embed model loaded")
    return _embed_model


def add_event(processed_event: dict):
    """
    Embed and store one event in ChromaDB.
    We create a rich text description that captures the key facts.
    """
    collection = get_collection()
    model      = get_embed_model()

    event_text = (
        f"Date: {processed_event.get('date', '')}\n"
        f"Event: {processed_event.get('actor1', '')} "
        f"{processed_event.get('event_label', '')} "
        f"{processed_event.get('actor2', '')}\n"
        f"Location: {processed_event.get('location', '')}\n"
        f"Hostility Score: {processed_event.get('goldstein_score', 0)}\n"
        f"Headline: {processed_event.get('article_title', '')}\n"
        f"Summary: {processed_event.get('article_text', '')[:300]}"
    )

    embedding = model.encode([event_text])[0].tolist()

    try:
        collection.add(
            embeddings=[embedding],
            documents=[event_text],
            metadatas=[{
                'date':       str(processed_event.get('date', '')),
                'actor1':     str(processed_event.get('actor1', '')),
                'actor2':     str(processed_event.get('actor2', '')),
                'event_type': str(processed_event.get('event_label', '')),
                'goldstein':  str(processed_event.get('goldstein_score', 0)),
                'source_url': str(processed_event.get('source_url', '')),
                'headline':   str(processed_event.get('article_title', ''))
            }],
            ids=[str(processed_event['gdelt_id'])]
        )
    except Exception as e:
        # ID already exists — update instead
        logger.debug(f"Event {processed_event['gdelt_id']} already in ChromaDB: {e}")


def semantic_search(query: str, n_results: int = 15) -> list[dict]:
    """
    Find events semantically similar to the query.
    Used by the RAG Q&A pipeline.
    """
    collection = get_collection()
    model      = get_embed_model()

    query_embedding = model.encode([query])[0].tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count() or 1)
    )

    if not results['documents'][0]:
        return []

    events = []
    for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
        events.append({
            'text':       doc,
            'source_url': meta.get('source_url', ''),
            'headline':   meta.get('headline', ''),
            'date':       meta.get('date', ''),
            'actor1':     meta.get('actor1', ''),
            'actor2':     meta.get('actor2', ''),
            'event_type': meta.get('event_type', ''),
            'goldstein':  meta.get('goldstein', '0')
        })

    return events


def rebuild_from_neo4j(neo4j_events: list[dict]):
    """
    Re-populate ChromaDB from Neo4j data.
    Called on server startup because ChromaDB is in-memory and doesn't persist.
    """
    logger.info(f"Rebuilding ChromaDB from {len(neo4j_events)} Neo4j events...")
    for event in neo4j_events:
        add_event(event)
    logger.info("ChromaDB rebuild complete")


def get_count() -> int:
    return get_collection().count()