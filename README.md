#  Diligence AI- Multi-Agent Due Diligence Engine


## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│         Drag-and-drop upload → Real-time progress →         │
│         Risk dashboard with agent deep-dive tabs            │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP
┌───────────────────────▼─────────────────────────────────────┐
│                    FastAPI Backend                           │
│         Job queue → Background processing                   │
└──────┬────────────────┬─────────────────┬────────────────┬──┘
       │                │                 │                │
  ┌────▼─────┐  ┌───────▼───┐  ┌─────────▼──┐  ┌─────────▼──┐
  │Financial │  │  Legal &  │  │ Reputation │  │    ESG &   │
  │  Agent   │  │Compliance │  │  & Media   │  │ Governance │
  └────┬─────┘  └───────┬───┘  └─────────┬──┘  └─────────┬──┘
       └────────────────┴─────────────────┴────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Master Reasoning    │
                    │       Agent           │
                    │  (Mistral Large)      │
                    └───────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Structured Report   │
                    │  Risk Score 0–100     │
                    │  Recommendation       │
                    │  Evidence Citations   │
                    └───────────────────────┘
```

## Features

- **4 Specialized Agents** running in parallel via `asyncio.gather()`
  - 💰 Financial Risk Agent — revenue trends, debt, cash position, anomalies
  - ⚖️ Legal & Compliance Agent — litigation, regulatory exposure, IP risk
  - 📰 Reputation & Media Agent — sentiment, controversy, narrative shifts
  - 🌱 ESG & Governance Agent — environmental flags, board issues, ethics

- **Master Reasoning Agent** — synthesizes all findings into:
  - Overall Risk Score (0–100)
  - Risk Rating (LOW → CRITICAL)
  - Investment Recommendation (RECOMMEND → AVOID)
  - Confidence Score
  - Executive Summary
  - Evidence-backed citations

- **Real-time progress tracking** via polling
- **Structured JSON output** with Pydantic validation
- **PDF, TXT, JSON** document support

---

## Quick Start

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Set your Mistral API key
cp .env.example .env
# Edit .env and add your MISTRAL_API_KEY

# Load env and start server
export $(cat .env | xargs)
python main.py
```

Backend runs at: `http://localhost:8000`

### 2. Frontend

Open `frontend/index.html` in your browser.

Set the backend URL to `http://localhost:8000` (default).

---

## Demo Flow (3 Minutes)

1. Open `frontend/index.html`
2. Enter company: **Tesla, Inc.**
3. Upload:
   - A Tesla financial report (PDF or TXT)
   - Any news article about Tesla
4. Click **Run Due Diligence Analysis**
5. Watch 4 agents process in real time
6. View the risk dashboard:
   - Overall Risk Score
   - Investment Recommendation
   - Per-agent findings with evidence

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analyze` | Upload documents + start analysis |
| `GET`  | `/status/{job_id}` | Poll analysis progress |

### POST /analyze

```
Content-Type: multipart/form-data

company_name: string
files: File[] (PDF, TXT, JSON)
```

### GET /status/{job_id}

```json
{
  "job_id": "job_1234567890",
  "status": "done",
  "progress": 100,
  "current_agent": null,
  "result": {
    "company_name": "Tesla, Inc.",
    "master": {
      "overall_risk_score": 62,
      "risk_rating": "ELEVATED",
      "investment_recommendation": "CAUTION",
      "confidence_score": 0.78,
      "executive_summary": "...",
      "key_risks": [...],
      "agent_scores": {
        "financial": 55,
        "legal": 70,
        "reputation": 60,
        "esg": 45
      }
    },
    "agents": {
      "financial": {...},
      "legal": {...},
      "reputation": {...},
      "esg": {...}
    }
  }
}
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Mistral Large (mistral-large-latest) |
| Backend | FastAPI + Python async |
| Document Parsing | pypdf |
| Agent Orchestration | asyncio.gather() (parallel) |
| Frontend | Vanilla HTML/CSS/JS |
| Structured Output | JSON schema + safe parser |



