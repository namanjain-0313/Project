# backend/api/rag.py
# RAG (Retrieval Augmented Generation) pipeline
# This is what powers the "ask anything" feature

import logging
import os
import google.generativeai as genai
from ..db import neo4j_client, chroma_client

logger = logging.getLogger(__name__)

def extract_keywords(question: str) -> list[str]:
    """
    Simple keyword extraction from the question.
    Used to search Neo4j alongside the semantic search.
    """
    # Countries and entities to look for
    known_entities = [
        "India", "China", "Pakistan", "Russia", "USA", "Bangladesh",
        "Nepal", "Sri Lanka", "Maldives", "Afghanistan",
        "Modi", "Xi", "LAC", "CPEC", "QUAD", "SCO", "BRICS",
        "Depsang", "Galwan", "Arunachal", "Kashmir", "Ladakh"
    ]
    question_lower = question.lower()
    return [e for e in known_entities if e.lower() in question_lower]


def answer_question(question: str) -> dict:
    """
    Full RAG pipeline for one user question.

    1. Semantic search in ChromaDB → find similar past events
    2. Entity-based search in Neo4j → find graph facts
    3. Combine into context
    4. Send to Gemini with context → get intelligence brief
    5. Return answer + sources
    """
    # Configure Gemini API
    api_key = os.environ.get("AIzaSyDjX38fExrldWQ3Ex8Ge8fLaIsSZ5hQT30")
    if not api_key:
        logger.error("AIzaSyDjX38fExrldWQ3Ex8Ge8fLaIsSZ5hQT30 is not set in environment variables.")
        return {
            "answer": "System Error: LLM API key not configured.",
            "sources": [],
            "events_searched": 0,
            "question": question
        }
        
    genai.configure(api_key=api_key)
    
    # Initialize the Gemini model
    model = genai.GenerativeModel('gemini-1.5-flash')

    # ── Step 1: ChromaDB semantic search ──────────────────
    similar_events = chroma_client.semantic_search(question, n_results=15)
    logger.info(f"ChromaDB returned {len(similar_events)} similar events")

    # ── Step 2: Neo4j graph search ─────────────────────────
    keywords = extract_keywords(question)
    graph_events = []

    for keyword in keywords[:3]:  # top 3 keywords only to limit data
        events = neo4j_client.get_events_for_country(keyword, limit=10)
        graph_events.extend(events)

    logger.info(f"Neo4j returned {len(graph_events)} graph events")

    # ── Step 3: Format context ─────────────────────────────
    context_parts = []

    if similar_events:
        context_parts.append("=== SEMANTICALLY SIMILAR EVENTS ===")
        for i, event in enumerate(similar_events[:10], 1):
            context_parts.append(
                f"{i}. [{event.get('date', 'N/A')}] {event.get('actor1', 'Unknown')} {event.get('event_type', 'interacted with')} {event.get('actor2', 'Unknown')}\n"
                f"   Headline: {event.get('headline', 'N/A')}\n"
                f"   Hostility: {event.get('goldstein', 'N/A')} | Source: {event.get('source_url', 'N/A')}"
            )

    if graph_events:
        context_parts.append("\n=== KNOWLEDGE GRAPH EVENTS ===")
        seen_ids = set()
        for event in graph_events[:10]:
            event_id = event.get('id', '')
            if event_id not in seen_ids:
                seen_ids.add(event_id)
                context_parts.append(
                    f"• [{event.get('date','')}] {event.get('actor1','')} → "
                    f"{event.get('event_type','')} → {event.get('actor2','')}\n"
                    f"  {event.get('headline','')} | {event.get('source_url','')}"
                )

    context = "\n".join(context_parts) if context_parts else "No relevant events found in knowledge base."

    # ── Step 4: Gemini generates the intelligence brief ────
    prompt = f"""You are a senior strategic intelligence analyst specializing in South Asian geopolitics, 
with a focus on India's national security interests.

Below is real, recent data from our global intelligence graph (sourced from GDELT and 
verified news articles). This data was collected and updated within the last 15 minutes.

{context}

---

Analyst Question: {question}

Write a concise intelligence brief answering this question. Structure your response as:

**SITUATION SUMMARY** (2-3 sentences: what is happening right now)

**KEY DEVELOPMENTS** (3-5 bullet points: specific recent events with dates)

**STRATEGIC IMPLICATION FOR INDIA** (1-2 sentences: what does this mean for India specifically)

**CONFIDENCE LEVEL**: [HIGH/MEDIUM/LOW] — based on how much relevant data was found

Base your answer ONLY on the provided context. If the context doesn't contain enough 
information, say so clearly. Do not add information from your training data."""

    try:
        # Generate the response using Gemini
        response = model.generate_content(prompt)
        answer_text = response.text

        # Collect unique source URLs
        sources = list(set(
            e.get('source_url', '') for e in similar_events
            if e.get('source_url', '').startswith('http')
        ))[:5]

        return {
            "answer": answer_text,
            "sources": sources,
            "events_searched": len(similar_events) + len(graph_events),
            "question": question
        }

    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return {
            "answer": "Sorry, the intelligence analysis service is temporarily unavailable.",
            "sources": [],
            "events_searched": 0,
            "question": question
        }