#!/usr/bin/env python3
# backend/seed_database.py
# Run this ONCE to load 30 days of historical data into Neo4j.
# After this, the real-time scheduler handles updates automatically.
#
# Usage:
#   cd backend
#   python seed_database.py
#
# This will take 15-30 minutes depending on your internet connection.
# You only need to run this once. Neo4j Aura persists the data forever.

import certifi
import os
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
import sys
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    # Verify environment variables
    required = ["NEO4J_URL", "NEO4J_PASSWORD", "GEMINI_API_KEY"]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        logger.error(f"Missing environment variables: {missing}")
        logger.error("Copy .env.example to .env and fill in your values")
        sys.exit(1)

    # Test Neo4j connection
    logger.info("Testing Neo4j connection...")
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            os.environ["NEO4J_URL"],
            auth=(
                os.environ.get("NEO4J_USERNAME", "neo4j"),
                os.environ["NEO4J_PASSWORD"]
            )
        )
        with driver.session() as session:
            session.run("RETURN 1")
        logger.info("Neo4j connection successful")
        driver.close()
    except Exception as e:
        logger.error(f"Cannot connect to Neo4j: {e}")
        logger.error("Check your NEO4J_URL and NEO4J_PASSWORD in .env")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("GOE Historical Data Loader")
    logger.info("This will download ~30 days of geopolitical events")
    logger.info("and load them into your Neo4j database.")
    logger.info("Expected time: 15-30 minutes")
    logger.info("=" * 60)

    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    logger.info(f"Loading {days} days of data...")

    from pipeline.orchestrator import run_historical_load
    run_historical_load(num_days=days)

    logger.info("=" * 60)
    logger.info("Seed complete! Your database is now populated.")
    logger.info("Deploy your backend to Render — it will start")
    logger.info("updating automatically every 15 minutes.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()