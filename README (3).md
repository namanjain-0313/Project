# Global Ontology Engine (GOE)
### India Strategic Intelligence Platform

Real-time geopolitical intelligence graph powered by GDELT, spaCy, Neo4j, and Claude API. Monitors 80,000+ global news sources every 15 minutes, extracts structured relationships between geopolitical entities, and surfaces intelligence insights through an interactive dashboard.

---

## What It Does

Most intelligence tools show you what happened. GOE shows you:
- **What it means** — structured relationships extracted from raw news
- **Who is coordinating narratives** — cross-country media synchronisation detection
- **What everyone is ignoring** — strategic events with high importance but low coverage
- **What will likely happen next** — grounded Q&A from live data, not LLM training memory

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Data source | GDELT Project | Global event feed, updated every 15 mins, free |
| Article fetching | newspaper3k | Full article text from GDELT source URLs |
| NLP — NER | spaCy (en_core_web_sm) | Extract entities from article text |
| NLP — Relations | Claude API (claude-opus-4-6) | Extract relationship triples from text |
| Entity resolution | sentence-transformers + rapidfuzz | Deduplicate entity mentions across articles |
| Graph database | Neo4j Aura Free (cloud) | Store knowledge graph permanently |
| Vector store | ChromaDB (in-memory) | Semantic search for RAG pipeline |
| RAG pipeline | Claude API | Generate grounded intelligence briefs |
| Backend API | FastAPI (Python) | REST endpoints serving frontend |
| Frontend | React + react-force-graph-2d + Recharts | Interactive dashboard |
| Backend hosting | Render.com (free tier) | 24/7 cloud server |
| Frontend hosting | Vercel (free tier) | CDN-served React app |
| Keep-alive | UptimeRobot (free) | Prevents Render free tier from sleeping |

---

## Project Structure

```
goe/
├── README.md
│
├── backend/
│   ├── main.py                        ← FastAPI app entry point + scheduler startup
│   ├── seed_database.py               ← One-time historical data loader (run once)
│   ├── render.yaml                    ← Render deployment configuration
│   ├── requirements.txt               ← All Python dependencies
│   ├── .env.example                   ← Template — copy to .env and fill in credentials
│   │
│   ├── pipeline/                      ← Data ingestion and NLP
│   │   ├── __init__.py
│   │   ├── constants.py               ← GDELT columns, CAMEO codes, canonical entities
│   │   ├── gdelt.py                   ← Download and filter GDELT files
│   │   ├── articles.py                ← Fetch full article text from source URLs
│   │   ├── nlp.py                     ← spaCy NER + Claude relation extraction
│   │   ├── resolution.py              ← Entity resolution to Wikidata IDs
│   │   └── orchestrator.py            ← Ties all pipeline stages together
│   │
│   ├── db/                            ← Database clients
│   │   ├── __init__.py
│   │   ├── neo4j_client.py            ← All Neo4j read/write operations
│   │   └── chroma_client.py           ← ChromaDB vector store operations
│   │
│   └── api/                           ← Intelligence endpoints
│       ├── __init__.py
│       ├── rag.py                     ← RAG Q&A pipeline (ChromaDB + Neo4j + Claude)
│       └── usp_analysis.py            ← USP 1: Narrative Warfare + USP 2: Blind Spots
│
└── frontend/
    ├── package.json
    ├── vercel.json                     ← Vercel deployment configuration
    ├── .env.example                    ← Template — copy to .env and set API URL
    └── src/
        ├── index.js                    ← React entry point + global styles
        ├── App.jsx                     ← Root layout (4-panel dashboard + chat)
        ├── api/
        │   └── client.js              ← All backend API calls in one place
        └── components/
            ├── RiskScores.jsx         ← Country relationship status panel
            ├── KnowledgeGraph.jsx     ← Interactive force-directed graph
            ├── EventFeed.jsx          ← Live scrolling event feed
            ├── IntelligenceChat.jsx   ← RAG-powered Q&A interface
            └── IntelligenceAlerts.jsx ← USP 1 + USP 2 alerts panel
```

---

## System Architecture

```
GDELT (public file server, updates every 15 mins)
        │
        │  Your scheduler downloads latest file
        ▼
Filter for India-relevant events (~200 per batch from ~5000)
        │
        │  For each event:
        ▼
Fetch full article from SourceURL       (pipeline/articles.py)
        │
        ▼
spaCy NER → extract entities            (pipeline/nlp.py)
        │
        ▼
Claude API → extract relationship triples
        │
        ▼
Entity resolution → map to Wikidata IDs (pipeline/resolution.py)
        │
        ├──────────────────────────────────────────┐
        ▼                                          ▼
Neo4j Aura (graph, persists forever)     ChromaDB (vectors, rebuilt on startup)
        │                                          │
        └──────────────────┬───────────────────────┘
                           │
                           │  FastAPI serves JSON to React
                           ▼
        4-panel dashboard + Intelligence Chat
        ┌─────────────┬──────────────┬────────────┬─────────────┐
        │ Risk Scores │ Knowledge    │ Event Feed │ Intelligence│
        │             │ Graph        │ (live)     │ Alerts      │
        │ China  ████ │              │            │ ⚠️ Narrative │
        │ Pak    ████ │  India─China │ • PLA      │ 🔍 Blind    │
        │ USA    ██   │    │         │   drills   │   Spots     │
        │ Russia ███  │  PLA─Depsang │   LAC      │             │
        └─────────────┴──────────────┴────────────┴─────────────┘
        ┌────────────────────────────────────────────────────────┐
        │  Q&A: "What is China doing near India?"               │
        │  → Situation brief + key events + sources ↗           │
        └────────────────────────────────────────────────────────┘
```

---

## Two USPs That Make This Different

### USP 1 — Narrative Warfare Detection
Detects when media from multiple countries is reporting the same topic with abnormally aligned tone simultaneously. Natural news coverage diverges. Coordinated campaigns converge. When Chinese state media, Pakistani outlets, and European independents all frame the same India story with the same sentiment within 48 hours, that synchronisation is flagged as a potential information operation.

**How the score works:** Groups events by actor pair. Averages tone per source country. Measures variance across countries. Low variance = high synchronisation. Boosts score if state media is involved. Alerts at threshold 0.55.

### USP 2 — Strategic Blind Spot Detector
Finds events that score high on strategic importance for India but low on media coverage. The gap between the two is the blind spot score. A China-Bangladesh port agreement with importance 8.7/10 and coverage 1.2/10 is a blind spot — strategically significant but flying under the radar.

**How the score works:** Importance = weighted formula using actor strategic weight + Goldstein magnitude + event type severity + India involvement. Coverage = normalised NumMentions and NumSources from GDELT. Blind spot = importance minus coverage.

---

## Data Flow

| Step | File | Input | Output |
|------|------|-------|--------|
| 1 | `gdelt.py` | GDELT public URL | Filtered pandas dataframe |
| 2 | `articles.py` | Source URLs from GDELT | Full article text |
| 3 | `nlp.py` — spaCy | Article text | Named entities list |
| 4 | `nlp.py` — Claude | Text + entities | Relationship triples JSON |
| 5 | `resolution.py` | Raw entity names | Canonical names + Wikidata IDs |
| 6 | `neo4j_client.py` | Resolved triples | Graph nodes and edges stored |
| 7 | `chroma_client.py` | Event text | Vectors stored for semantic search |
| Q&A | `rag.py` | User question | ChromaDB + Neo4j → Claude → answer |
| USP | `usp_analysis.py` | Neo4j events | Narrative alerts + blind spots |

---

## Setup Guide

### Step 1 — Create Free Accounts

You need five accounts. All free.

| Service | URL | What you get |
|---------|-----|-------------|
| Neo4j Aura | aura.neo4j.io | Free cloud graph database |
| Anthropic | console.anthropic.com | Claude API key (add $5 credit) |
| Render | render.com | Backend hosting |
| Vercel | vercel.com | Frontend hosting |
| UptimeRobot | uptimerobot.com | Keep Render awake |

**Neo4j setup:** Create account → New Instance → AuraDB Free → Save the connection URL and password immediately (shown only once). Format: `neo4j+s://xxxxxxxx.databases.neo4j.io`

---

### Step 2 — Local Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Set up environment variables
cp .env.example .env
# Open .env and fill in:
# NEO4J_URL, NEO4J_PASSWORD, ANTHROPIC_API_KEY

# Seed database with 30 days of historical data (run ONCE, takes 20-30 mins)
python seed_database.py

# Start backend locally
uvicorn main:app --reload --port 8000

# Verify it works
curl http://localhost:8000/health
# Should return: {"status": "ok", "chroma_events": 1234}
```

---

### Step 3 — Local Frontend Setup

```bash
cd frontend

npm install

# Copy env template
cp .env.example .env
# .env content: REACT_APP_API_URL=http://localhost:8000

npm start
# Opens http://localhost:3000
```

---

### Step 4 — Deploy Backend to Render

1. Push `backend/` folder to a GitHub repo named `goe-backend`
2. Go to render.com → New → Web Service
3. Connect `goe-backend` repo
4. Configure:
   - **Build Command:** `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Region:** Singapore (closest to India)
   - **Plan:** Free
5. Add Environment Variables in Render dashboard:
   ```
   NEO4J_URL         = neo4j+s://xxxxxxxx.databases.neo4j.io
   NEO4J_PASSWORD    = your-password
   NEO4J_USERNAME    = neo4j
   ANTHROPIC_API_KEY = sk-ant-xxxxxxxx
   ENVIRONMENT       = production
   LOG_LEVEL         = INFO
   ```
6. Click Deploy → wait 5-10 minutes
7. Test: `https://goe-backend.onrender.com/health`

---

### Step 5 — Set Up UptimeRobot

Render free tier sleeps after 15 minutes of inactivity. UptimeRobot prevents this by pinging your backend every 5 minutes.

1. Go to uptimerobot.com → Register free
2. Add New Monitor:
   - Type: HTTP(s)
   - Name: GOE Backend
   - URL: `https://goe-backend.onrender.com/health`
   - Interval: 5 minutes
3. Save

Your backend now runs 24/7 without sleeping.

---

### Step 6 — Deploy Frontend to Vercel

1. Push `frontend/` folder to a GitHub repo named `goe-frontend`
2. Go to vercel.com → New Project → Import `goe-frontend`
3. Add Environment Variable:
   ```
   REACT_APP_API_URL = https://goe-backend.onrender.com
   ```
4. Click Deploy
5. Dashboard live at: `https://goe-frontend.vercel.app`

---

### Step 7 — Seed Production Database

After Render is deployed, run seed_database.py from your laptop pointing at the production Neo4j:

```bash
cd backend
# Your .env already has the production Neo4j credentials
python seed_database.py
# This loads 30 days of historical data directly into Neo4j Aura
# Takes 20-30 minutes
# After this the Render scheduler handles all future updates automatically
```

---

## API Endpoints

| Method | Endpoint | Purpose | Used By |
|--------|----------|---------|---------|
| GET | `/health` | System status + event count | UptimeRobot, status bar |
| GET | `/api/events/latest` | Last 50 events | Event Feed panel |
| GET | `/api/events/country/{name}` | Events for one country | Country drill-down |
| GET | `/api/graph` | Nodes + edges for visualization | Knowledge Graph panel |
| GET | `/api/risk-scores` | Hostility scores per country | Risk Scores panel |
| GET | `/api/timeline/{country}` | Daily score trend | Timeline chart |
| POST | `/api/query` | RAG Q&A — takes question, returns brief | Intelligence Chat |
| GET | `/api/intelligence-alerts` | USP 1 + USP 2 combined | Intelligence Alerts panel |
| GET | `/api/narrative-warfare` | Narrative warfare alerts only | Direct access |
| GET | `/api/blind-spots` | Strategic blind spots only | Direct access |

---

## Frontend Components

| Component | Panel | Data Source | Refresh |
|-----------|-------|-------------|---------|
| `RiskScores.jsx` | Top left | `/api/risk-scores` | Every 5 mins |
| `KnowledgeGraph.jsx` | Center | `/api/graph` | On load |
| `EventFeed.jsx` | Right | `/api/events/latest` | Every 60 secs |
| `IntelligenceAlerts.jsx` | Far right | `/api/intelligence-alerts` | Every 15 mins |
| `IntelligenceChat.jsx` | Bottom | `/api/query` | On user input |

---

## Team Division of Work

| Person | Files They Own |
|--------|---------------|
| ML / NLP | `pipeline/nlp.py`, `pipeline/resolution.py`, `pipeline/constants.py` |
| Data Engineer | `pipeline/gdelt.py`, `pipeline/articles.py`, `seed_database.py` |
| Graph Engineer | `db/neo4j_client.py`, `pipeline/orchestrator.py` |
| RAG + USP | `db/chroma_client.py`, `api/rag.py`, `api/usp_analysis.py` |
| Backend + DevOps | `main.py`, `render.yaml`, Render setup, UptimeRobot |
| Frontend | All files in `frontend/src/` |

---

## Demo Script (Hackathon)

**Setup:** Open `https://goe-frontend.vercel.app` on a large screen. Have the Intelligence Alerts panel visible.

**Step 1 — Establish credibility (30 seconds)**
Point to the LIVE indicator and event count in the top bar. Say: "This dashboard updated 8 minutes ago. Everything you see is sourced from real news articles from the last 15 minutes to 30 days."

**Step 2 — Knowledge graph (45 seconds)**
Zoom in on the India node in the center panel. Show its connections. Say: "Each edge here is a relationship extracted from a real article by our NLP pipeline — spaCy found the entities, Claude extracted how they relate. Red edges are hostile, green are cooperative."

**Step 3 — Risk scores (20 seconds)**
Point to the left panel. Say: "This is the average Goldstein hostility score over 14 days. Pakistan is in the red. USA is green. These numbers update automatically as new events come in."

**Step 4 — Narrative warfare (60 seconds)**
Click the Intelligence Alerts panel, Narrative tab. If there is a CRITICAL alert, click it to expand. Say: "Our system detected that media from 4 countries is reporting on this India-China situation with 84% tone synchronisation. Natural coverage diverges. This level of alignment is a statistical signature of a coordinated information operation. No other system in this room can show you this."

**Step 5 — Blind spots (45 seconds)**
Click the Blind Spots tab. Show the top result. Say: "This event scored 8.7 out of 10 on strategic importance for India but only 1.2 out of 10 on media coverage. Only 3 articles globally mentioned it. Our system found it because it looks at what matters, not just what is loud."

**Step 6 — Live Q&A (60 seconds)**
Type in the chat: `"What military actions has China taken near India in the last 7 days?"`
While it loads say: "This is not ChatGPT. Claude is reading 23 real events from our knowledge base that were collected in the last 48 hours. Every fact in the answer will have a source URL you can click and verify."
Show the answer. Show the source links.

**Closing line:**
"Every other team built a news dashboard with a chatbot. GOE detects who is coordinating narratives, surfaces what everyone is ignoring, and answers questions from live intelligence — not from training data that is months old."

---

## Key Technical Decisions and Why

**Why GDELT over scraping news directly?**
GDELT already ran NLP on 80,000 sources and gives you structured event data for free. Building your own scraper for that scale would take months.

**Why Claude for relation extraction instead of a fine-tuned model?**
Fine-tuning a relation extraction model on geopolitical data requires labelled training data you don't have and weeks of work. Claude does it zero-shot via the API in 2 days of integration.

**Why Neo4j instead of PostgreSQL?**
Geopolitical intelligence is fundamentally about connections — who talked to whom, what connects to what, indirect effects across 3 hops. Graph databases do this natively. SQL requires JOIN operations that grow exponentially with path depth.

**Why ChromaDB in-memory instead of persisted?**
For a prototype, rebuilding ChromaDB from Neo4j on startup (takes 2 minutes) is acceptable. The data is already in Neo4j permanently. ChromaDB is just an index for fast semantic search.

**Why Render free tier instead of a paid server?**
Free tier is enough for a hackathon prototype. UptimeRobot solves the sleep problem. The architecture is identical — moving to a paid tier later is one config change.

---

## Environment Variables Reference

| Variable | Where to get it | Example |
|----------|----------------|---------|
| `NEO4J_URL` | Neo4j Aura dashboard after creating instance | `neo4j+s://abc123.databases.neo4j.io` |
| `NEO4J_USERNAME` | Always `neo4j` for Aura | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j Aura dashboard — save immediately, shown once | `AbCdEfGh12345` |
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys | `sk-ant-api03-...` |
| `ENVIRONMENT` | Set manually | `production` or `development` |
| `LOG_LEVEL` | Set manually | `INFO` or `DEBUG` |

---

## Troubleshooting

**Backend starts but event count is 0**
You have not run `seed_database.py` yet. Run it from your laptop with your `.env` credentials filled in. Takes 20-30 minutes.

**`ModuleNotFoundError: No module named 'pipeline'`**
You are running uvicorn from the wrong directory. You must run it from inside the `backend/` folder, not from the project root.

**`Neo4j connection failed`**
Check that `NEO4J_URL` starts with `neo4j+s://` not `bolt://`. Aura uses `neo4j+s`. Also verify the password has no trailing spaces.

**Graph visualization is empty**
The graph endpoint returned nodes but no edges, meaning events were saved but relation extraction produced no triples. Check that `ANTHROPIC_API_KEY` is set correctly and has credit.

**Render keeps sleeping despite UptimeRobot**
Check UptimeRobot is actually pinging `/health` and getting a 200 response. If the first ping after sleep takes too long, Render may return a timeout. Switch UptimeRobot interval to 4 minutes.

**Frontend shows OFFLINE in status bar**
The backend URL in your Vercel environment variable is wrong, or CORS is blocking requests. Verify `REACT_APP_API_URL` in Vercel matches your exact Render URL with no trailing slash.
