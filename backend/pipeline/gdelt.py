# backend/pipeline/gdelt.py
# Downloads GDELT files, filters for India-relevant events

import requests
import zipfile
import io
import pandas as pd
import logging
from datetime import datetime, timedelta
from .constants import GDELT_COLUMNS, STRATEGIC_COUNTRY_CODES, STRATEGIC_GEO_CODES

logger = logging.getLogger(__name__)

# Track processed files so we never process the same file twice
_processed_files = set()


def get_latest_gdelt_url() -> str:
    """
    GDELT publishes a text file every 15 mins telling you the URL of the latest data.
    We read that file to get the URL.
    """
    response = requests.get(
        "http://data.gdeltproject.org/gdeltv2/lastupdate.txt",
        timeout=10
    )
    response.raise_for_status()

    # File has 3 lines. First line = events file.
    # Each line looks like:
    # 1047884 7c9e2b... http://data.gdeltproject.org/gdeltv2/20240315120000.export.CSV.zip
    first_line = response.text.strip().split('\n')[0]
    url = first_line.strip().split(' ')[2]
    return url


def download_gdelt_zip(url: str) -> pd.DataFrame | None:
    """Download a GDELT zip file from a URL and return as DataFrame"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        csv_filename = zip_file.namelist()[0]

        df = pd.read_csv(
            zip_file.open(csv_filename),
            sep='\t',
            header=None,
            names=GDELT_COLUMNS,
            dtype=str,
            on_bad_lines='skip'
        )
        return df

    except Exception as e:
        logger.error(f"Failed to download GDELT file {url}: {e}")
        return None


def filter_india_relevant(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only events relevant to India's strategic interests.
    Converts numeric fields and drops rows with no source URL.
    """
    # Convert numeric columns
    df['GoldsteinScale'] = pd.to_numeric(df['GoldsteinScale'], errors='coerce')
    df['NumMentions']    = pd.to_numeric(df['NumMentions'],    errors='coerce')
    df['AvgTone']        = pd.to_numeric(df['AvgTone'],        errors='coerce')
    df['SQLDATE']        = pd.to_datetime(df['SQLDATE'], format='%Y%m%d', errors='coerce')

    # Filter: keep if any strategic country is involved as actor or location
    actor_mask = (
        df['Actor1CountryCode'].isin(STRATEGIC_COUNTRY_CODES) |
        df['Actor2CountryCode'].isin(STRATEGIC_COUNTRY_CODES)
    )
    geo_mask = (
        df['Actor1Geo_CountryCode'].isin(STRATEGIC_GEO_CODES) |
        df['Actor2Geo_CountryCode'].isin(STRATEGIC_GEO_CODES) |
        df['ActionGeo_CountryCode'].isin(STRATEGIC_GEO_CODES)
    )

    filtered = df[actor_mask | geo_mask].copy()

    # Must have a source URL to be useful
    filtered = filtered.dropna(subset=['SOURCEURL'])
    filtered = filtered[filtered['SOURCEURL'].str.startswith('http')]

    # Drop very low-mention events (likely noise)
    filtered = filtered[filtered['NumMentions'].fillna(0) >= 2]

    logger.info(f"Filtered {len(df)} rows → {len(filtered)} India-relevant events")
    return filtered.reset_index(drop=True)


def fetch_realtime_batch() -> pd.DataFrame | None:
    """
    Check if there's a new GDELT file. If yes, download and return it.
    If we've already processed this file, return None.
    Called every 15 minutes by the scheduler.
    """
    try:
        url = get_latest_gdelt_url()

        if url in _processed_files:
            logger.debug(f"Already processed {url}, skipping")
            return None

        logger.info(f"New GDELT file detected: {url}")
        df = download_gdelt_zip(url)

        if df is not None:
            _processed_files.add(url)
            return filter_india_relevant(df)

    except Exception as e:
        logger.error(f"Real-time fetch failed: {e}")

    return None


def fetch_historical_days(num_days: int = 30) -> pd.DataFrame:
    """
    Download the last N days of GDELT data.
    Run this ONCE when you first set up the system to seed the database.
    After that, use fetch_realtime_batch() for updates.

    Note: Each day file is ~30-60MB zipped. 30 days = ~1-2GB download.
    This takes 10-20 minutes depending on your connection.
    """
    all_frames = []
    today = datetime.now()

    for i in range(1, num_days + 1):
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y%m%d')

        # Daily files use a different URL pattern than real-time files
        url = f"http://data.gdeltproject.org/events/{date_str}.export.CSV.zip"

        logger.info(f"Downloading historical day {i}/{num_days}: {date_str}")

        df = download_gdelt_zip(url)
        if df is not None:
            filtered = filter_india_relevant(df)
            all_frames.append(filtered)
            logger.info(f"  {date_str}: {len(filtered)} relevant events")

    if not all_frames:
        logger.error("No historical data downloaded")
        return pd.DataFrame()

    combined = pd.concat(all_frames, ignore_index=True)
    logger.info(f"Historical load complete: {len(combined)} total events over {num_days} days")
    return combined