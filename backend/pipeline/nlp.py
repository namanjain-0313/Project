# Updated `nlp.py`

# backend/pipeline/nlp.py
# Step 1: spaCy NER — extracts entities from article text
# Step 2: Gemini API — extracts relationship triples from text + entities

import json
import logging
import os
from typing import Optional

# pip install google-generativeai
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Load spaCy model once at module level (expensive to load repeatedly)
_nlp = None

def get_nlp():
    """Lazy-load spaCy model"""
    global _nlp
    if _nlp is None:
        import spacy
        try:
            # Transformer model — more accurate but slower
            _nlp = spacy.load("en_core_web_trf")
            logger.info("Loaded spaCy transformer model")
        except OSError:
            # Fall back to smaller model if transformer not installed
            try:
                _nlp = spacy.load("en_core_web_lg")
                logger.info("Loaded spaCy lg model")
            except OSError:
                _nlp = spacy.load("en_core_web_sm")
                logger.info("Loaded spaCy sm model (least accurate)")
    return _nlp


def extract_entities_spacy(text: str) -> list[dict]:
    """
    Run spaCy NER on article text.
    Returns list of {text, label, start, end}
    """
    nlp = get_nlp()

    # Truncate to 10,000 chars — spaCy has memory limits
    doc = nlp(text[:10000])

    entities = []
    seen = set()

    for ent in doc.ents:
        # Skip very short entities (usually noise)
        if len(ent.text.strip()) < 2:
            continue

        # Deduplicate — same text+label pair
        key = (ent.text.strip().lower(), ent.label_)
        if key in seen:
            continue
        seen.add(key)

        entities.append({
            'text': ent.text.strip(),
            'label': ent.label_,
            'start': ent.start_char,
            'end': ent.end_char
        })

    return entities


def extract_relations_llm(
    article_text: str,
    entities: list[dict],
    gdelt_actor1: str,
    gdelt_actor2: str,
    gdelt_event_label: str,
    gdelt_goldstein: float
) -> list[dict]:
    """
    Send article text + entities to the Gemini API.
    Returns structured relationship triples natively as JSON.
    """
    # Configure API key from environment variables
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY missing from environment variables.")
        return []
        
    genai.configure(api_key=api_key)

    # Initialize Gemini 1.5 Flash (Fast, excellent for extraction, generous free tier)
    # Forcing response_mime_type to application/json guarantees structured output
    model = genai.GenerativeModel(
        'gemini-1.5-flash',
        generation_config={"response_mime_type": "application/json"}
    )

    # Format entity list for the prompt
    entity_lines = "\n".join([
        f"  - {e['text']} ({e['label']})"
        for e in entities[:30]  # limit to 30 most important
    ])

    prompt = f"""You are an intelligence analyst specializing in South Asian geopolitics.

GDELT pre-classified this article as:
- Actor 1: {gdelt_actor1}
- Actor 2: {gdelt_actor2}  
- Event type: {gdelt_event_label}
- Hostility score: {gdelt_goldstein} (scale: -10 = war, 0 = neutral, +10 = full cooperation)

Additional entities found in the article:
{entity_lines}

Article text:
{article_text[:3000]}

Extract ALL meaningful relationships between the entities above.
Focus on: diplomatic actions, military movements, economic agreements, 
political statements, territorial disputes, and alliance formations.

Return an array of JSON objects. Each object must have exactly these fields:
- "subject": the entity performing the action (string)
- "relation": relationship type in UPPER_SNAKE_CASE (string)  
- "object": the entity receiving the action (string)
- "confidence": your confidence 0.0 to 1.0 (number)
- "quote": a short direct quote from the article supporting this (string, max 100 chars)

Good relation types: WARNED, THREATENED, SIGNED_AGREEMENT, DEPLOYED_FORCES_AT,
IMPOSED_SANCTIONS_ON, HELD_TALKS_WITH, CONDEMNED, SUPPORTED, REJECTED_CLAIMS_OF,
CONDUCTED_EXERCISE_NEAR, DEMANDED, ACCUSED, INVESTED_IN, WITHDREW_FROM"""

    try:
        response = model.generate_content(prompt)
        
        # Because we used JSON mode, the response is guaranteed to be a valid JSON string
        triples = json.loads(response.text)

        # Validate structure and filter out low confidence
        valid_triples = []
        for t in triples:
            if all(k in t for k in ['subject', 'relation', 'object', 'confidence']):
                # Cast confidence to float just in case the LLM returned a string "0.8"
                if float(t['confidence']) >= 0.6:  
                    valid_triples.append(t)

        logger.info(f"LLM extracted {len(valid_triples)} valid triples")
        return valid_triples

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from LLM: {e}\nRaw output: {response.text}")
        return []
    except Exception as e:
        logger.error(f"LLM API call failed: {e}")
        return []


def process_article(
    article_text: str,
    article_title: str,
    gdelt_row: dict
) -> dict:
    """
    Full NLP processing of one article.
    Runs spaCy NER then LLM relation extraction.

    Returns processed event dict ready for Neo4j + ChromaDB.
    """
    try:
        from .constants import CAMEO_LOOKUP
    except ImportError:
        # Fallback if constants file isn't found during testing
        CAMEO_LOOKUP = {}

    event_code = str(gdelt_row.get('EventCode', ''))
    event_label = CAMEO_LOOKUP.get(event_code, f"Event code {event_code}")

    # Step 1: spaCy NER
    full_text = f"{article_title}\n\n{article_text}"
    entities = extract_entities_spacy(full_text)

    # Step 2: LLM relation extraction
    triples = extract_relations_llm(
        article_text=full_text,
        entities=entities,
        gdelt_actor1=str(gdelt_row.get('Actor1Name', '')),
        gdelt_actor2=str(gdelt_row.get('Actor2Name', '')),
        gdelt_event_label=event_label,
        gdelt_goldstein=float(gdelt_row.get('GoldsteinScale', 0) or 0)
    )

    return {
        'gdelt_id': str(gdelt_row.get('GLOBALEVENTID', '')),
        'date': str(gdelt_row.get('SQLDATE', '')),
        'actor1': str(gdelt_row.get('Actor1Name', '')),
        'actor2': str(gdelt_row.get('Actor2Name', '')),
        'event_code': event_code,
        'event_label': event_label,
        'goldstein_score': float(gdelt_row.get('GoldsteinScale', 0) or 0),
        'avg_tone': float(gdelt_row.get('AvgTone', 0) or 0),
        'num_mentions': int(gdelt_row.get('NumMentions', 0) or 0),
        'location': str(gdelt_row.get('ActionGeo_FullName', '')),
        'source_url': str(gdelt_row.get('SOURCEURL', '')),
        'article_title': article_title,
        'article_text': article_text[:500],  # store excerpt only
        'entities': entities,
        'triples': triples
    }