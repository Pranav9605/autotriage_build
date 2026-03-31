# AutoTriage Backend

AI-powered SAP incident triage platform (FastAPI + PostgreSQL + Claude).

## Setup

See the playbook for full setup instructions.

## Quick Start

```bash
cp .env.example .env
# Edit .env with real API keys
pip install -r requirements.txt
alembic upgrade head
python scripts/seed_db.py
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs
