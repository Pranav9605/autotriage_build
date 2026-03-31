"""Seed the AutoTriage database with tenant, synthetic tickets, KB articles, and eval holdout.

Usage:
  python scripts/seed_db.py                  # Full seed with embeddings
  python scripts/seed_db.py --skip-embeddings  # Seed without calling embedding API
  python scripts/seed_db.py --dry-run          # Validate data without inserting

Requirements:
  - PostgreSQL running with pgvector extension
  - Migrations applied: alembic upgrade head
  - .env file with DATABASE_URL and OPENAI_API_KEY
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import select

from app.config import get_settings
from app.core.tenant_config import load_tenant_config
from app.database import get_db
from app.models.eval_golden_set import EvalGoldenSet
from app.models.kb_article import KBArticle
from app.models.model_version import ModelVersion
from app.models.tenant import Tenant
from app.models.ticket import Ticket
from app.utils.enrichment import enrich_ticket
from app.utils.id_generator import generate_ticket_id, generate_uuid

DATA_DIR = Path(__file__).parent / "data"
TENANT_ID = "patil_group"
BATCH_SIZE = 10  # embedding batch size to avoid rate limits
RATE_LIMIT_DELAY = 0.5  # seconds between embedding batches


def load_json(filename: str) -> list:
    path = DATA_DIR / filename
    if not path.exists():
        print(f"ERROR: {path} not found. Run the generate scripts first.")
        sys.exit(1)
    return json.loads(path.read_text())


async def seed(skip_embeddings: bool = False, dry_run: bool = False) -> None:
    settings = get_settings()

    # Embedding service
    embedding_service = None
    if not skip_embeddings:
        from app.services.embedding import OpenAIEmbeddingService
        embedding_service = OpenAIEmbeddingService(api_key=settings.OPENAI_API_KEY)

    # Load data files
    synthetic_tickets = load_json("synthetic_tickets.json")
    eval_holdout = load_json("eval_holdout.json")
    kb_articles_data = load_json("kb_articles.json")

    print(f"Loaded: {len(synthetic_tickets)} tickets, {len(kb_articles_data)} KB articles, "
          f"{len(eval_holdout)} holdout tickets")

    if dry_run:
        print("\nDRY RUN — validating data structure only, no DB inserts.")
        _validate_tickets(synthetic_tickets)
        _validate_tickets(eval_holdout)
        _validate_kb_articles(kb_articles_data)
        print("All data validated successfully.")
        return

    async for db in get_db():
        # -----------------------------------------------------------------
        # 1. Tenant record
        # -----------------------------------------------------------------
        print(f"\n[1/6] Creating tenant: {TENANT_ID}")
        existing_tenant = await db.execute(
            select(Tenant).where(Tenant.id == TENANT_ID)
        )
        if existing_tenant.scalar_one_or_none() is None:
            cfg = load_tenant_config(TENANT_ID)
            tenant = Tenant(
                id=TENANT_ID,
                name=cfg.display_name,
                config=cfg.model_dump(),
            )
            db.add(tenant)
            await db.commit()
            print(f"  Created tenant: {cfg.display_name}")
        else:
            print(f"  Tenant already exists, skipping.")

        # -----------------------------------------------------------------
        # 2. Synthetic tickets (working set)
        # -----------------------------------------------------------------
        print(f"\n[2/6] Seeding {len(synthetic_tickets)} synthetic tickets...")
        tickets_inserted = 0
        descriptions = [t["raw_text"] for t in synthetic_tickets]

        embeddings: list = [None] * len(descriptions)
        if embedding_service:
            print(f"  Generating embeddings in batches of {BATCH_SIZE}...")
            for i in range(0, len(descriptions), BATCH_SIZE):
                batch = descriptions[i: i + BATCH_SIZE]
                batch_embeddings = await embedding_service.embed_batch(batch)
                for j, emb in enumerate(batch_embeddings):
                    embeddings[i + j] = emb
                print(f"  Embedded {min(i + BATCH_SIZE, len(descriptions))}/{len(descriptions)}")
                if i + BATCH_SIZE < len(descriptions):
                    time.sleep(RATE_LIMIT_DELAY)

        for idx, ticket_data in enumerate(synthetic_tickets):
            enriched = enrich_ticket(ticket_data["raw_text"])
            ticket = Ticket(
                id=generate_ticket_id(),
                tenant_id=TENANT_ID,
                source=ticket_data["source"],
                raw_text=ticket_data["raw_text"],
                description=ticket_data["raw_text"],
                tcode=enriched.get("tcode"),
                error_code=enriched.get("error_code"),
                environment=ticket_data.get("environment") or enriched.get("environment"),
                reporter=ticket_data.get("reporter"),
                status="open",
                embedding=embeddings[idx],
                ground_truth_module=ticket_data["ground_truth_module"],
                ground_truth_priority=ticket_data["ground_truth_priority"],
            )
            db.add(ticket)
            tickets_inserted += 1

        await db.commit()
        print(f"  Inserted {tickets_inserted} tickets.")

        # -----------------------------------------------------------------
        # 3. KB articles
        # -----------------------------------------------------------------
        print(f"\n[3/6] Seeding {len(kb_articles_data)} KB articles...")
        kb_texts = [f"{a['title']}\n{a['content']}" for a in kb_articles_data]
        kb_embeddings: list = [None] * len(kb_texts)

        if embedding_service:
            print(f"  Generating KB embeddings...")
            for i in range(0, len(kb_texts), BATCH_SIZE):
                batch = kb_texts[i: i + BATCH_SIZE]
                batch_embeddings = await embedding_service.embed_batch(batch)
                for j, emb in enumerate(batch_embeddings):
                    kb_embeddings[i + j] = emb
                if i + BATCH_SIZE < len(kb_texts):
                    time.sleep(RATE_LIMIT_DELAY)

        kb_inserted = 0
        for idx, article in enumerate(kb_articles_data):
            kb = KBArticle(
                id=generate_uuid(),
                tenant_id=TENANT_ID,
                title=article["title"],
                content=article["content"],
                module=article["module"],
                error_codes=article["error_codes"] or None,
                tcodes=article["tcodes"] or None,
                tags=article["tags"] or None,
                embedding=kb_embeddings[idx],
            )
            db.add(kb)
            kb_inserted += 1

        await db.commit()
        print(f"  Inserted {kb_inserted} KB articles.")

        # -----------------------------------------------------------------
        # 4. Eval holdout set (eval_golden_set table)
        # -----------------------------------------------------------------
        print(f"\n[4/6] Seeding {len(eval_holdout)} eval holdout records...")
        for ticket_data in eval_holdout:
            enriched = enrich_ticket(ticket_data["raw_text"])
            golden = EvalGoldenSet(
                id=generate_uuid(),
                tenant_id=TENANT_ID,
                ticket_text=ticket_data["raw_text"],
                structured_fields={
                    "source": ticket_data["source"],
                    "reporter": ticket_data.get("reporter"),
                    "tcode": enriched.get("tcode"),
                    "error_code": enriched.get("error_code"),
                    "environment": ticket_data.get("environment") or enriched.get("environment"),
                },
                true_module=ticket_data["ground_truth_module"],
                true_priority=ticket_data["ground_truth_priority"],
                source="synthetic",
                is_active=True,
            )
            db.add(golden)

        await db.commit()
        print(f"  Inserted {len(eval_holdout)} eval holdout records.")

        # -----------------------------------------------------------------
        # 5. Initial model version record
        # -----------------------------------------------------------------
        print(f"\n[5/6] Creating baseline model version record...")
        existing_mv = await db.execute(
            select(ModelVersion).where(
                ModelVersion.tenant_id == TENANT_ID,
                ModelVersion.version == "baseline_llm_only",
            )
        )
        if existing_mv.scalar_one_or_none() is None:
            mv = ModelVersion(
                id=generate_uuid(),
                tenant_id=TENANT_ID,
                model_type="llm_triage",
                version="baseline_llm_only",
                training_samples=0,
                holdout_accuracy=0.0,
                is_active=True,
                config={"llm_model": "claude-sonnet-4-20250514", "note": "baseline before feedback"},
            )
            db.add(mv)
            await db.commit()
            print("  Created baseline model version.")
        else:
            print("  Model version already exists, skipping.")

        # -----------------------------------------------------------------
        # 6. Summary
        # -----------------------------------------------------------------
        print(f"\n[6/6] Seeding complete!")
        print(f"  Tenant       : {TENANT_ID}")
        print(f"  Tickets      : {tickets_inserted}")
        print(f"  KB articles  : {kb_inserted}")
        print(f"  Eval holdout : {len(eval_holdout)}")
        print(f"  Model version: baseline_llm_only")
        print(f"  Embeddings   : {'YES' if embedding_service else 'SKIPPED (--skip-embeddings)'}")
        break  # exit the async generator


def _validate_tickets(tickets: list) -> None:
    required = {"source", "raw_text", "reporter", "ground_truth_module", "ground_truth_priority"}
    for i, t in enumerate(tickets):
        missing = required - set(t.keys())
        if missing:
            print(f"ERROR: Ticket {i} missing fields: {missing}")
            sys.exit(1)
    print(f"  Validated {len(tickets)} tickets OK")


def _validate_kb_articles(articles: list) -> None:
    required = {"title", "content", "module", "error_codes", "tcodes", "tags"}
    for i, a in enumerate(articles):
        missing = required - set(a.keys())
        if missing:
            print(f"ERROR: KB article {i} missing fields: {missing}")
            sys.exit(1)
    print(f"  Validated {len(articles)} KB articles OK")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed AutoTriage database")
    parser.add_argument("--skip-embeddings", action="store_true",
                        help="Insert records without embedding vectors")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate data files without inserting")
    args = parser.parse_args()

    asyncio.run(seed(
        skip_embeddings=args.skip_embeddings,
        dry_run=args.dry_run,
    ))
