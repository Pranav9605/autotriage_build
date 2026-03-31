# CLAUDE.md — AutoTriage Project Context

## What This Is
AutoTriage: AI-powered SAP incident triage platform.
Customer 0: Patil Group (on-premise SAP S/4HANA, India).
I am building the FastAPI backend. Frontend (Next.js + shadcn) exists separately.

## Architecture (Memorize This)
Ticket Intake → Enrichment → Hybrid Retrieval (pgvector+FTS) → LLM Triage (Claude) → Rule Override → Store → Feedback Loop

## Tech Stack
- Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic
- PostgreSQL + pgvector + pg_trgm
- Claude Sonnet (Anthropic API) for triage
- Pydantic v2 for all schemas
- text-embedding-3-small (OpenAI) for embeddings

## Non-Negotiable Rules
1. tenant_id on EVERY database table, EVERY query, EVERY API call. No exceptions.
2. All LLM interaction through abstract TriageEngine interface. Never call Claude directly from routes.
3. Pydantic schemas for ALL request/response. No raw dicts crossing API boundaries.
4. Hybrid search = semantic (pgvector cosine) + lexical (tsvector) + exact boost (error_code, tcode). Threshold-gated at 0.78 minimum.
5. Confidence has two fields: raw (from LLM) and calibrated (empirically adjusted). Both stored.
6. Feedback stores FULL AI prediction snapshot + human decision. Not just the diff.
7. Rule overrides applied AFTER AI classification, BEFORE output. Rules from YAML, never hardcoded.
8. Every new file needs proper error handling, logging, and type hints.

## Database Tables
tenants, tickets, triage_decisions, feedback, kb_articles, model_versions, eval_golden_set
All have tenant_id column. All queries filter by tenant_id.

## SAP Module Taxonomy
FI (Finance), MM (Materials), SD (Sales), PP (Production), BASIS (Infra), ABAP (Dev), PI_PO (Integration), HR, CUSTOM

## Key File Locations
- Tenant config: config/{tenant_id}.yaml
- Main app: app/main.py
- All routes: app/api/
- Business logic: app/services/
- ORM models: app/models/
- Pydantic schemas: app/schemas/

## Current Build Phase
Phase: Phase 5 — Synthetic Data COMPLETE
Last completed: Phase 5 — Synthetic Data + Seeding + KB Articles
Next up: Phase 6 — Integration Testing + End-to-End Flows

## Phase 1 Key Files
- app/models/base.py — TimestampMixin, TenantMixin
- app/models/{tenant,ticket,triage_decision,feedback,kb_article,model_version,eval_golden_set}.py
- alembic/versions/0001_initial_schema.py — all tables, extensions, hybrid_search fn, triggers
- alembic/env.py — async migrations with model discovery

## Phase 5 Key Files
- scripts/generate_synthetic.py — 100 SAP tickets (80 working + 20 holdout), deterministic seed
- scripts/generate_kb_articles.py — 30 SAP KB articles with genuine troubleshooting content
- scripts/seed_db.py — seeds tenant, tickets (with embeddings), KB, eval_golden_set, model_version; flags: --skip-embeddings, --dry-run
- scripts/run_eval.py — hits live API, measures module/priority accuracy, prints confusion matrix, saves eval_results.json
- scripts/data/synthetic_tickets.json — 80 working set tickets
- scripts/data/eval_holdout.json — 20 holdout tickets
- scripts/data/kb_articles.json — 30 KB articles
- Note: Module distribution: FI=30, BASIS=20, MM=15, SD=15, PI_PO=10, ABAP=10
- Note: Priority distribution: P1=15, P2=32, P3=39, P4=14

## Phase 4 Key Files
- app/dependencies.py — DI singletons (embedding, triage engine) + per-request deps
- app/schemas/{ticket,feedback,kb,dashboard}.py — all Pydantic schemas
- app/services/feedback_service.py — FeedbackService.create_feedback()
- app/services/dashboard_service.py — KPI, module accuracy, confidence distribution
- app/api/health.py — GET /api/v1/health (DB + LLM + embedding checks)
- app/api/tickets.py — POST/GET /api/v1/tickets, GET /api/v1/tickets/{id}
- app/api/triage.py — POST/GET /api/v1/tickets/{id}/triage
- app/api/feedback.py — POST /api/v1/triage/{id}/feedback, GET /api/v1/feedback
- app/api/kb.py — GET /search, POST/PUT/GET /articles, GET /articles/{id}
- app/api/dashboard.py — GET /kpis, /module-accuracy, /confidence-distribution
- app/api/admin.py — GET/PUT /tenant/config, GET /models/versions
- app/api/router.py — all routers aggregated
- app/main.py — CORS, TenantMiddleware, RequestLoggingMiddleware, exception handlers

## Phase 3 Key Files
- app/schemas/triage.py — TriageDecisionSchema (with review_reason), TriageRequest, TriageResponse
- app/services/triage_engine.py — TriageEngine (ABC), ClaudeTriageEngine (with tenacity retry + correction prompt)
- app/services/rule_engine.py — RuleEngine.apply_rules() (all rules fire, last-wins overrides)
- app/services/intake.py — IntakeService.process_ticket() (full 13-step pipeline)
- tests/test_rules.py — 10 tests, all passing
- tests/test_triage.py — 14 tests, all passing (engine + pipeline, all mocked)
- Note: app/models/ticket.py tenant_id now has ForeignKey("tenants.id") (bug fix from Phase 1)
- Note: Rule engine evaluates ALL conditions against original decision; overrides accumulate (last wins)

## Phase 2 Key Files
- app/utils/id_generator.py — generate_ticket_id(), generate_uuid()
- app/utils/enrichment.py — extract_tcode(), extract_error_code(), extract_environment(), enrich_ticket()
- app/core/exceptions.py — AutoTriageException hierarchy
- app/core/tenant_config.py — TenantConfig Pydantic model, load_tenant_config(), get_team_for_module()
- app/core/middleware.py — TenantMiddleware, RequestLoggingMiddleware
- app/schemas/triage.py — RetrievalResult, TriageRequest, TriageDecisionSchema, TriageResponse
- app/services/embedding.py — EmbeddingService (ABC), OpenAIEmbeddingService (with tenacity retry)
- app/services/retrieval.py — RetrievalService.search_similar() via hybrid_search SQL function
- tests/test_enrichment.py — 39 tests, all passing
- tests/test_retrieval.py — 6 tests, all passing

## Commands
- Run server: uvicorn app.main:app --reload
- Run tests: pytest -v
- Run migrations: alembic upgrade head
- Generate migration: alembic revision --autogenerate -m "description"
- Seed data: python scripts/seed_db.py
