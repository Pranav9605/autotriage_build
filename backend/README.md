# AutoTriage Backend

AI-powered SAP incident triage platform. AutoTriage classifies incoming support tickets by SAP module (FI, MM, SD, BASIS, ABAP, …) and priority (P1–P4) using Claude (Anthropic), enriches them with semantically similar past tickets and KB articles via pgvector hybrid search, and applies configurable hard-rule overrides — all in a single API call.

Built for **Patil Group** (Customer 0): on-premise SAP S/4HANA, India. Designed to reduce mean-time-to-triage from hours to seconds and improve routing accuracy through consultant feedback loops.

---

## Prerequisites

| Dependency | Version |
|---|---|
| Python | 3.11+ |
| PostgreSQL | 15+ with **pgvector** and **pg_trgm** extensions |
| Anthropic API key | Claude Sonnet (for triage) |
| OpenAI API key | text-embedding-3-small (for semantic search) |

---

## Setup

```bash
# 1. Clone and create virtualenv
python -m venv myenv && source myenv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env          # fill in DATABASE_URL, ANTHROPIC_API_KEY, OPENAI_API_KEY

# 4. Create PostgreSQL database and enable extensions
psql -U postgres -c "CREATE DATABASE autotriage;"
psql -U postgres -d autotriage -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql -U postgres -d autotriage -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"

# 5. Run migrations
alembic upgrade head

# 6. Seed synthetic data (optional — 80 tickets, 30 KB articles)
python scripts/generate_synthetic.py
python scripts/generate_kb_articles.py
python scripts/seed_db.py          # full seed with embeddings
# or:
python scripts/seed_db.py --skip-embeddings   # fast, no embedding API needed
```

---

## Running the Server

```bash
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs`

---

## Running Tests

```bash
pytest tests/ -v
# Expected: 93 passed
```

No database required — all tests use mocked dependencies.

---

## Demo Script

With the server running:

```bash
python scripts/demo.py
```

Creates 3 tickets (FI, WhatsApp/vague, ABAP+PRD), submits feedback, prints dashboard KPIs, and searches KB articles.

---

## Real-Time Updates (SSE)

```bash
# Terminal 1 — subscribe to events
curl -N -H "X-Tenant-Id: patil_group" http://localhost:8000/api/v1/tickets/stream

# Terminal 2 — create a ticket
curl -X POST http://localhost:8000/api/v1/tickets \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: patil_group" \
  -d '{"source": "chat", "raw_text": "FB50 posting error F5 301 in production system", "reporter": "Rahul Patil"}'
```

Terminal 1 receives a `ticket_triaged` SSE event immediately.

---

## Architecture

```
Ticket Intake
    → Enrichment (tcode, error_code, environment extraction)
    → Embed (OpenAI text-embedding-3-small)
    → Hybrid Retrieval (pgvector cosine + tsvector FTS + exact boost)
    → LLM Triage (Claude Sonnet — module, priority, root cause, solution)
    → Rule Override (YAML-defined hard rules, last-wins)
    → Persist (tickets + triage_decisions, all tenant-scoped)
    → Feedback Loop (consultant accept/override → training signal)
```

**Key design decisions:**
- `tenant_id` on every table, every query, every API call — isolation is non-negotiable
- Confidence stored as both raw (LLM) and calibrated (empirical adjustment)
- Feedback stores the full AI prediction snapshot, not just the diff
- Rules evaluate against the original LLM decision; overrides accumulate (last wins)
- All LLM calls go through the abstract `TriageEngine` interface — never called directly from routes

For full architecture and build context see `CLAUDE.md`.
