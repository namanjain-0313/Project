# Global Ontology Engine (GOE)
### India Strategic Intelligence Platform

Real-time geopolitical intelligence graph powered by GDELT, spaCy, Neo4j, and Claude.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Data source | GDELT Project | Global event feed, updated every 15 mins |
| Article fetching | newspaper3k | Full article text from GDELT source URLs |
| NLP — NER | spaCy (en_core_web_sm) | Extract entities from article text |
| NLP — Relations | Claude API (claude-opus-4-6) | Extract relationship triples |
| Entity resolution | sentence-transformers + rapidfuzz | Deduplicate entity mentions |
| Graph database | Neo4j Aura (cloud) | Store knowledge graph permanently |
| Vector store | ChromaDB (in-memory) | Semantic search for RAG |
| RAG pipeline | Claude API | Generate intelligence briefs |
| Backend API | FastAPI (Python) | REST endpoints for frontend |
| Frontend | React + react-force-graph-2d | Dashboard UI |
| Backend hosting | Render.com (free tier) | 24/7 cloud server |
| Frontend hosting | Vercel (free tier) | CDN-served React app |
| Keep-alive | UptimeRobot (free) | Prevents Render from sleeping |

---

## Project Structure

```
goe/
├── backend/
│   ├── main.py                   ← FastAPI app + startup logic
│   ├── seed_database.py          ← One-time historical data loader
│   ├── render.yaml               ← Render deployment config
│   ├── requirements.txt          ← Python dependencies
│   ├── .env.example              ← Copy to .env for local dev
│   │
│   ├── pipeline/
│   │   ├── constants.py          ← GDELT columns, CAMEO codes, entity dict
│   │   ├── gdelt.py              ← Download + filter GDELT files
│   │   ├── articles.py           ← Fetch article text from URLs
│   │   ├── nlp.py                ← spaCy NER + Claude relation extraction
│   │   ├── resolution.py         ← Entity resolution to Wikidata IDs
│   │   └── orchestrator.py       ← Ties all pipeline stages together
│   │
│   ├── db/
│   │   ├── neo4j_client.py       ← All Neo4j read/write operations
│   │   └── chroma_client.py      ← ChromaDB vector store operations
│   │
│   └── api/
│       └── rag.py                ← RAG Q&A pipeline
│
└── frontend/
    ├── package.json
    ├── vercel.json               ← Vercel deployment config
    ├── .env.example
    └── src/
        ├── index.js              ← React entry point
        ├── App.jsx               ← Root layout (4-panel dashboard)
        ├── api/
        │   └── client.js         ← All backend API calls
        └── components/
            ├── RiskScores.jsx    ← Country relationship status panel
            ├── KnowledgeGraph.jsx ← Interactive force-directed graph
            ├── EventFeed.jsx     ← Live scrolling event feed
            └── IntelligenceChat.jsx ← RAG-powered Q&A interface
```

---

## Setup — Step by Step

### Step 1: Accounts to Create (all free)

1. **Neo4j Aura** — https://aura.neo4j.io
   - Create account → New Instance → Free → AuraDB Free
   - Save the connection URL and password — you only see it once
   - Format: `neo4j+s://xxxxxxxx.databases.neo4j.io`

2. **Anthropic** — https://console.anthropic.com
   - Create account → API Keys → Create Key
   - Add $5 credit (enough for entire hackathon)

3. **Render** — https://render.com (for backend)
4. **Vercel** — https://vercel.com (for frontend)
5. **UptimeRobot** — https://uptimerobot.com (free keep-alive)
6. **GitHub** — two repos: `goe-backend` and `goe-frontend`

---

### Step 2: Local Development Setup

```bash
# Clone / create your repo
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Set up environment variables
cp .env.example .env
# Edit .env and fill in NEO4J_URL, NEO4J_PASSWORD, ANTHROPIC_API_KEY

# Seed the database with 30 days of historical data (run ONCE)
python seed_database.py

# Start the backend locally
uvicorn main:app --reload --port 8000

# Test it works
curl http://localhost:8000/health
```

```bash
# Frontend setup
cd frontend
npm install
cp .env.example .env
# Edit .env: REACT_APP_API_URL=http://localhost:8000

npm start
# Opens http://localhost:3000
```

---

### Step 3: Deploy Backend to Render

1. Push backend folder to GitHub repo `goe-backend`
2. Go to render.com → New → Web Service
3. Connect your `goe-backend` GitHub repo
4. Settings:
   - **Build Command:** `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Region:** Singapore (closest to India)
5. Environment Variables (add these in Render dashboard):
   ```
   NEO4J_URL       = neo4j+s://xxxxxxxx.databases.neo4j.io
   NEO4J_PASSWORD  = your-password
   NEO4J_USERNAME  = neo4j
   ANTHROPIC_API_KEY = sk-ant-xxxxxxxx
   ENVIRONMENT     = production
   ```
6. Click Deploy
7. Wait 5-10 minutes for first deploy
8. Test: `https://goe-backend.onrender.com/health`

---

### Step 4: Set Up UptimeRobot (keeps Render awake)

1. Go to uptimerobot.com → Register
2. Add New Monitor:
   - Monitor Type: HTTP(s)
   - Friendly Name: GOE Backend
   - URL: `https://goe-backend.onrender.com/health`
   - Monitoring Interval: 5 minutes
3. Save — done. Render will never sleep again.

---

### Step 5: Deploy Frontend to Vercel

1. Push frontend folder to GitHub repo `goe-frontend`
2. Go to vercel.com → New Project
3. Import `goe-frontend` repo
4. Environment Variables:
   ```
   REACT_APP_API_URL = https://goe-backend.onrender.com
   ```
5. Click Deploy
6. Your dashboard is live at: `https://goe-frontend.vercel.app`

---

## Data Flow (How Everything Connects)

```
GDELT (public file server, updates every 15 mins)
        │
        │ Backend scheduler downloads latest file
        ▼
Filter for India-relevant events (~200 per batch)
        │
        │ For each event:
        ▼
Fetch full article from SourceURL (newspaper3k)
        │
        ▼
spaCy NER → extract entities from article text
        │
        ▼
Claude API → extract relationship triples
        │
        ▼
Entity resolution → map names to Wikidata IDs
        │
        ├──→ Neo4j Aura (graph, persists forever)
        └──→ ChromaDB (vectors, rebuilt on startup)
                │
                │ Frontend polls backend every 60 secs
                ▼
        FastAPI serves JSON to React dashboard
                │
                ▼
        4 panels update in real time:
        - Risk scores (5 min refresh)
        - Knowledge graph (on load)
        - Event feed (60 sec refresh)
        - Q&A chat (on demand)
```

---

## Demo Script (for hackathon)

1. Open `https://goe-frontend.vercel.app` on a large screen
2. Point out the LIVE indicator and last-updated timestamp
3. Show the knowledge graph — zoom in on India node, show connections
4. Point to risk scores — explain what the numbers mean
5. Scroll the event feed — show real headlines with source links
6. Type in chat: **"What military actions has China taken near India in the last 7 days?"**
7. Show the answer arriving with citations
8. Type: **"How is the China-Pakistan Economic Corridor affecting India's strategic position?"**
9. Point out: this answer is grounded in real events from the last 2 weeks, not ChatGPT's training data

**Key talking point:** "Every answer you see is sourced from real news articles collected in the last 15 minutes. The graph behind it has [X] entities and [Y] relationships. This is not a demo with fake data."

---

## Team Responsibilities

| Person | Files They Own |
|--------|---------------|
| ML Engineer (You) | `pipeline/nlp.py`, `pipeline/resolution.py` |
| Data Engineer | `pipeline/gdelt.py`, `pipeline/articles.py`, `seed_database.py` |
| Graph Engineer | `db/neo4j_client.py`, `pipeline/orchestrator.py` |
| RAG Engineer | `db/chroma_client.py`, `api/rag.py` |
| Backend/DevOps | `main.py`, `render.yaml`, Render + UptimeRobot setup |
| Frontend | All files in `frontend/src/` |
