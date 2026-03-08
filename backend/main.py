# backend/main.py
# Entry point — Render runs this file with: uvicorn main:app --host 0.0.0.0 --port 8000

import logging
import os
import threading
import time
import schedule
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env file for local development
# On Render, environment variables are set in the dashboard instead
load_dotenv()

# Set up logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Import our modules
from pipeline.orchestrator import run_realtime_update
from db import neo4j_client, chroma_client
from api.rag import answer_question
from api.usp_analysis import get_intelligence_alerts, detect_narrative_warfare, find_blind_spots


# ─── STARTUP / SHUTDOWN ──────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup and shutdown"""

    logger.info("=== GOE Backend Starting ===")

    # 1. Test database connections
    if not neo4j_client.test_connection():
        logger.error("Cannot connect to Neo4j — check NEO4J_URL and NEO4J_PASSWORD")
    else:
        logger.info("Neo4j connection OK")

    # 2. Rebuild ChromaDB from Neo4j (since ChromaDB is in-memory)
    logger.info("Rebuilding ChromaDB from Neo4j data...")
    try:
        recent_events = neo4j_client.get_latest_events(limit=500)
        if recent_events:
            chroma_client.rebuild_from_neo4j(recent_events)
            logger.info(f"ChromaDB rebuilt with {len(recent_events)} events")
        else:
            logger.warning("Neo4j is empty — run historical load first")
    except Exception as e:
        logger.error(f"ChromaDB rebuild failed: {e}")

    # 3. Start background GDELT scheduler
    def run_scheduler():
        schedule.every(15).minutes.do(run_realtime_update)
        logger.info("GDELT scheduler started — will run every 15 minutes")

        # Run once immediately on startup
        run_realtime_update()

        while True:
            schedule.run_pending()
            time.sleep(30)

    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Background scheduler thread started")

    logger.info("=== GOE Backend Ready ===")

    yield  # App is running

    logger.info("GOE Backend shutting down")


# ─── APP SETUP ───────────────────────────────────────────────────

app = FastAPI(
    title="Global Ontology Engine API",
    description="Real-time geopolitical intelligence for India",
    version="1.0.0",
    lifespan=lifespan
)

# CORS — allows the React frontend (Vercel) to call this backend (Render)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://goe-frontend.vercel.app",   # your Vercel URL
        "http://localhost:3000",              # local development
        "*"                                   # remove in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── REQUEST / RESPONSE MODELS ───────────────────────────────────

class QueryRequest(BaseModel):
    question: str


# ─── ENDPOINTS ───────────────────────────────────────────────────

@app.get("/health")
def health_check():
    """
    UptimeRobot pings this every 5 minutes to keep Render awake.
    Also used to verify the service is running.
    """
    return {
        "status": "ok",
        "service": "Global Ontology Engine",
        "chroma_events": chroma_client.get_count()
    }


@app.get("/api/events/latest")
def get_latest_events(limit: int = Query(default=50, le=200)):
    """
    Returns the most recent geopolitical events.
    Frontend polls this every 60 seconds to update the live feed.
    """
    try:
        events = neo4j_client.get_latest_events(limit=limit)
        return {"events": events, "count": len(events)}
    except Exception as e:
        logger.error(f"get_latest_events failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/events/country/{country_name}")
def get_events_by_country(country_name: str, limit: int = 30):
    """Returns events involving a specific country"""
    try:
        events = neo4j_client.get_events_for_country(country_name, limit=limit)
        return {"events": events, "country": country_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph")
def get_graph_data():
    """
    Returns nodes and edges for the frontend graph visualization.
    react-force-graph consumes this format directly.
    """
    try:
        data = neo4j_client.get_graph_data()
        return data
    except Exception as e:
        logger.error(f"get_graph_data failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/risk-scores")
def get_risk_scores():
    """
    Returns risk scores for India's key strategic relationships.
    Based on average Goldstein score of recent events.
    """
    try:
        scores = neo4j_client.get_risk_scores()
        return {"scores": scores}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/timeline/{country}")
def get_timeline(country: str, days: int = Query(default=30, le=90)):
    """
    Returns daily hostility score trend for a country.
    Used for the relationship timeline chart.
    """
    try:
        timeline = neo4j_client.get_timeline(country, days=days)
        return {"timeline": timeline, "country": country, "days": days}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query")
def query_intelligence(request: QueryRequest):
    """
    Main Q&A endpoint.
    Takes a natural language question, searches the knowledge base,
    and returns an AI-generated intelligence brief with sources.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        result = answer_question(request.question)
        return result
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── USP ENDPOINTS ───────────────────────────────────────────────

@app.get("/api/intelligence-alerts")
def get_alerts():
    """
    USP 1 + USP 2 combined.
    Returns narrative warfare alerts and strategic blind spots.
    Frontend calls this on load and every 15 minutes.
    Works entirely on existing Neo4j data — no new infrastructure.
    """
    try:
        return get_intelligence_alerts()
    except Exception as e:
        logger.error(f"Intelligence alerts failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/narrative-warfare")
def get_narrative_warfare_alerts():
    """
    USP 1 only — Narrative Warfare Detection.
    Returns coordinated narrative campaigns detected across
    multiple countries media in the last 48 hours.
    """
    try:
        alerts = detect_narrative_warfare(hours_back=48)
        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        logger.error(f"Narrative warfare detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/blind-spots")
def get_blind_spot_alerts():
    """
    USP 2 only — Strategic Blind Spot Detector.
    Returns events that are strategically important for India
    but are receiving very little media coverage.
    """
    try:
        spots = find_blind_spots(days_back=7)
        return {"blind_spots": spots, "count": len(spots)}
    except Exception as e:
        logger.error(f"Blind spot detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))