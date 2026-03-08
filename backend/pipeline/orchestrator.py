# backend/pipeline/orchestrator.py
# Ties all pipeline stages together into one function.
# Called by the scheduler every 15 minutes.

import logging
from .gdelt import fetch_realtime_batch, fetch_historical_days
from .articles import fetch_articles_batch
from .nlp import process_article
from .resolution import resolve_triples
from ..db import neo4j_client, chroma_client

logger = logging.getLogger(__name__)


def process_gdelt_batch(df) -> int:
    """
    Process a batch of GDELT rows through the full pipeline.
    Returns number of events successfully processed.

    Pipeline:
    1. Get article text from SourceURL
    2. Run spaCy NER on full article text
    3. Send to Claude for relation extraction
    4. Resolve entities to canonical Wikidata IDs
    5. Save to Neo4j graph
    6. Embed and save to ChromaDB
    """
    if df is None or df.empty:
        return 0

    # Step 1: Fetch articles
    urls = df['SOURCEURL'].dropna().unique().tolist()
    logger.info(f"Fetching {len(urls)} articles...")
    articles = fetch_articles_batch(urls, delay=0.3)
    logger.info(f"Got {len(articles)} articles successfully")

    processed_count = 0

    for _, row in df.iterrows():
        url = str(row.get('SOURCEURL', ''))
        article = articles.get(url)

        try:
            if article:
                # Full pipeline — we have the article text
                processed = process_article(
                    article_text=article['text'],
                    article_title=article['title'],
                    gdelt_row=row.to_dict()
                )
            else:
                # Fallback — use only GDELT fields, no article text
                from .constants import CAMEO_LOOKUP
                event_code = str(row.get('EventCode', ''))
                processed = {
                    'gdelt_id':       str(row.get('GLOBALEVENTID', '')),
                    'date':           str(row.get('SQLDATE', '')),
                    'actor1':         str(row.get('Actor1Name', '')),
                    'actor2':         str(row.get('Actor2Name', '')),
                    'event_code':     event_code,
                    'event_label':    CAMEO_LOOKUP.get(event_code, 'Unknown event'),
                    'goldstein_score':float(row.get('GoldsteinScale', 0) or 0),
                    'avg_tone':       float(row.get('AvgTone', 0) or 0),
                    'num_mentions':   int(row.get('NumMentions', 0) or 0),
                    'location':       str(row.get('ActionGeo_FullName', '')),
                    'source_url':     url,
                    'article_title':  '',
                    'article_text':   '',
                    'entities':       [],
                    'triples':        []
                }

            # Resolve entities + save
            resolved_triples = resolve_triples(processed.get('triples', []))
            neo4j_client.save_event(processed, resolved_triples)
            chroma_client.add_event(processed)
            processed_count += 1

        except Exception as e:
            logger.error(f"Failed to process event {row.get('GLOBALEVENTID')}: {e}")
            continue

    logger.info(f"Batch complete: {processed_count}/{len(df)} events processed")
    return processed_count


def run_realtime_update():
    """
    Called by scheduler every 15 minutes.
    Downloads the latest GDELT file and processes new events.
    """
    logger.info("=== Running real-time GDELT update ===")
    df = fetch_realtime_batch()

    if df is None or df.empty:
        logger.info("No new GDELT data")
        return

    count = process_gdelt_batch(df)
    logger.info(f"=== Update complete: {count} new events added ===")


def run_historical_load(num_days: int = 30):
    """
    One-time historical seed.
    Run this manually ONCE to populate the database with past data.
    After that, run_realtime_update() handles ongoing updates.

    Usage:
        from backend.pipeline.orchestrator import run_historical_load
        run_historical_load(30)
    """
    logger.info(f"=== Starting historical load: {num_days} days ===")
    df = fetch_historical_days(num_days)

    if df.empty:
        logger.error("No historical data fetched")
        return

    # Process in batches of 100 to avoid memory issues
    batch_size = 100
    total = len(df)

    for start in range(0, total, batch_size):
        batch = df.iloc[start:start + batch_size]
        logger.info(f"Processing batch {start//batch_size + 1}/{(total//batch_size) + 1}")
        process_gdelt_batch(batch)

    logger.info("=== Historical load complete ===")