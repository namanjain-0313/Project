# backend/pipeline/articles.py
# Fetches full article text from URLs found in GDELT's SOURCEURL field

import logging
import time
from typing import Optional
import requests

logger = logging.getLogger(__name__)

# Sites known to be paywalled - skip immediately, don't waste time
PAYWALLED_DOMAINS = [
    'nytimes.com', 'ft.com', 'bloomberg.com', 'wsj.com',
    'economist.com', 'theatlantic.com', 'washingtonpost.com'
]

# Minimum article length - anything shorter is probably a login page
MIN_ARTICLE_LENGTH = 200


def is_paywalled(url: str) -> bool:
    return any(domain in url for domain in PAYWALLED_DOMAINS)


def fetch_article(url: str) -> Optional[dict]:
    """
    Fetches and parses a news article from a URL.
    Returns dict with title, text, publish_date - or None if failed.

    We use newspaper3k which handles:
    - HTML stripping
    - Main content extraction (ignores nav, ads, footers)
    - Date parsing
    - Encoding issues
    """
    if is_paywalled(url):
        logger.debug(f"Skipping paywalled URL: {url}")
        return None

    try:
        # Import here so server starts even if newspaper3k has issues
        from newspaper import Article

        article = Article(url, request_timeout=10)
        article.download()
        article.parse()

        text = article.text.strip()

        if len(text) < MIN_ARTICLE_LENGTH:
            logger.debug(f"Article too short ({len(text)} chars), likely paywalled: {url}")
            return None

        return {
            'url': url,
            'title': article.title or '',
            'text': text,
            'publish_date': article.publish_date,
            'top_image': article.top_image or ''
        }

    except Exception as e:
        logger.debug(f"Failed to fetch article {url}: {e}")
        return None


def fetch_articles_batch(urls: list[str], delay: float = 0.5) -> dict[str, dict]:
    """
    Fetch multiple articles with a small delay between requests
    so we don't hammer news sites.

    Returns dict: {url: article_data}
    Only includes successfully fetched articles.
    """
    results = {}
    success = 0
    failed = 0

    for i, url in enumerate(urls):
        article = fetch_article(url)

        if article:
            results[url] = article
            success += 1
        else:
            failed += 1

        # Small delay to be a polite web citizen
        if delay > 0 and i < len(urls) - 1:
            time.sleep(delay)

        # Log progress every 20 articles
        if (i + 1) % 20 == 0:
            logger.info(f"  Articles: {i+1}/{len(urls)} — {success} success, {failed} failed")

    logger.info(f"Article batch complete: {success} success, {failed} failed out of {len(urls)}")
    return results