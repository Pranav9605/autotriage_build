"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # Extensions
    # ------------------------------------------------------------------ #
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ------------------------------------------------------------------ #
    # tenants
    # ------------------------------------------------------------------ #
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tenants"),
    )

    # ------------------------------------------------------------------ #
    # tickets
    # ------------------------------------------------------------------ #
    op.create_table(
        "tickets",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("tcode", sa.String(), nullable=True),
        sa.Column("error_code", sa.String(), nullable=True),
        sa.Column("environment", sa.String(), nullable=True),
        sa.Column("system_id", sa.String(), nullable=True),
        sa.Column("reporter", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="open"),
        sa.Column("embedding", postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.Column("ground_truth_module", sa.String(), nullable=True),
        sa.Column("ground_truth_priority", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_tickets"),
    )
    # Use raw SQL for the vector column type (pgvector)
    op.execute("ALTER TABLE tickets ALTER COLUMN embedding TYPE vector(1536) USING NULL")
    op.create_index("ix_tickets_tenant_id", "tickets", ["tenant_id"])
    op.create_index("ix_tickets_tenant_status", "tickets", ["tenant_id", "status"])
    op.create_index(
        "ix_tickets_search_vector", "tickets", ["search_vector"], postgresql_using="gin"
    )
    op.create_index(
        "ix_tickets_error_code",
        "tickets",
        ["error_code"],
        postgresql_where=sa.text("error_code IS NOT NULL"),
    )
    op.create_index(
        "ix_tickets_tcode",
        "tickets",
        ["tcode"],
        postgresql_where=sa.text("tcode IS NOT NULL"),
    )
    # ivfflat index — created after data is loaded; listed here for completeness
    # op.execute(
    #     "CREATE INDEX ix_tickets_embedding ON tickets "
    #     "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 20)"
    # )

    # ------------------------------------------------------------------ #
    # triage_decisions
    # ------------------------------------------------------------------ #
    op.create_table(
        "triage_decisions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("ticket_id", sa.String(), sa.ForeignKey("tickets.id"), nullable=False),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("module", sa.String(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("issue_type", sa.String(), nullable=False),
        sa.Column("root_cause_hypothesis", sa.Text(), nullable=True),
        sa.Column("recommended_solution", sa.Text(), nullable=True),
        sa.Column("assign_to", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("confidence_calibrated", sa.Float(), nullable=True),
        sa.Column("classification_source", sa.String(), nullable=False),
        sa.Column("model_version", sa.String(), nullable=False),
        sa.Column("rules_applied", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("similar_ticket_ids", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("similar_ticket_scores", postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column("kb_article_ids", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("manual_review_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("review_reason", sa.String(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("llm_tokens_used", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_triage_decisions"),
        sa.UniqueConstraint("ticket_id", "version", name="uq_triage_ticket_version"),
    )
    op.create_index("ix_triage_decisions_ticket_id", "triage_decisions", ["ticket_id"])
    op.create_index("ix_triage_decisions_tenant_id", "triage_decisions", ["tenant_id"])

    # ------------------------------------------------------------------ #
    # feedback
    # ------------------------------------------------------------------ #
    op.create_table(
        "feedback",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("ticket_id", sa.String(), sa.ForeignKey("tickets.id"), nullable=False),
        sa.Column(
            "triage_decision_id",
            sa.String(),
            sa.ForeignKey("triage_decisions.id"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("overrides", sa.JSON(), nullable=True),
        sa.Column("override_category", sa.String(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("consultant_id", sa.String(), nullable=False),
        sa.Column(
            "decided_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("decision_latency_seconds", sa.Float(), nullable=True),
        sa.Column("final_module", sa.String(), nullable=False),
        sa.Column("final_priority", sa.String(), nullable=False),
        sa.Column("final_assign_to", sa.String(), nullable=False),
        sa.Column("is_correct_module", sa.Boolean(), nullable=False),
        sa.Column("is_correct_priority", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_feedback"),
    )
    op.create_index("ix_feedback_ticket_id", "feedback", ["ticket_id"])
    op.create_index("ix_feedback_triage_decision_id", "feedback", ["triage_decision_id"])
    op.create_index("ix_feedback_tenant_id", "feedback", ["tenant_id"])

    # ------------------------------------------------------------------ #
    # kb_articles
    # ------------------------------------------------------------------ #
    op.create_table(
        "kb_articles",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("module", sa.String(), nullable=False),
        sa.Column("error_codes", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("tcodes", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("embedding", postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_kb_articles"),
    )
    op.execute("ALTER TABLE kb_articles ALTER COLUMN embedding TYPE vector(1536) USING NULL")
    op.create_index("ix_kb_articles_tenant_id", "kb_articles", ["tenant_id"])
    op.create_index(
        "ix_kb_articles_search_vector",
        "kb_articles",
        ["search_vector"],
        postgresql_using="gin",
    )

    # ------------------------------------------------------------------ #
    # model_versions
    # ------------------------------------------------------------------ #
    op.create_table(
        "model_versions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("model_type", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("training_samples", sa.Integer(), nullable=False),
        sa.Column("holdout_accuracy", sa.Float(), nullable=False),
        sa.Column("module_f1_weighted", sa.Float(), nullable=True),
        sa.Column("priority_exact_match", sa.Float(), nullable=True),
        sa.Column("calibration_error", sa.Float(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "trained_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_model_versions"),
    )
    op.create_index("ix_model_versions_tenant_id", "model_versions", ["tenant_id"])

    # ------------------------------------------------------------------ #
    # eval_golden_set
    # ------------------------------------------------------------------ #
    op.create_table(
        "eval_golden_set",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("ticket_text", sa.Text(), nullable=False),
        sa.Column("structured_fields", sa.JSON(), nullable=False),
        sa.Column("true_module", sa.String(), nullable=False),
        sa.Column("true_priority", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id", name="pk_eval_golden_set"),
    )
    op.create_index("ix_eval_golden_set_tenant_id", "eval_golden_set", ["tenant_id"])

    # ------------------------------------------------------------------ #
    # hybrid_search PostgreSQL function
    # ------------------------------------------------------------------ #
    op.execute("""
CREATE OR REPLACE FUNCTION hybrid_search(
    p_tenant_id TEXT,
    p_query_embedding vector(1536),
    p_query_text TEXT,
    p_error_code TEXT DEFAULT NULL,
    p_tcode TEXT DEFAULT NULL,
    p_environment TEXT DEFAULT NULL,
    p_min_score FLOAT DEFAULT 0.78,
    p_limit INT DEFAULT 3
)
RETURNS TABLE (
    result_id TEXT,
    result_type TEXT,
    title TEXT,
    content TEXT,
    final_score FLOAT,
    semantic_score FLOAT,
    lexical_score FLOAT,
    exact_boost FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH combined AS (
        SELECT
            t.id AS result_id,
            'ticket'::TEXT AS result_type,
            t.id AS title,
            t.description AS content,
            1 - (t.embedding <=> p_query_embedding) AS sem_score,
            COALESCE(ts_rank(t.search_vector, plainto_tsquery('english', p_query_text)), 0) AS lex_score,
            (CASE WHEN p_error_code IS NOT NULL AND t.error_code = p_error_code THEN 0.3 ELSE 0 END
             + CASE WHEN p_tcode IS NOT NULL AND t.tcode = p_tcode THEN 0.2 ELSE 0 END) AS ex_boost
        FROM tickets t
        WHERE t.tenant_id = p_tenant_id
            AND (p_environment IS NULL OR t.environment = p_environment)
            AND t.embedding IS NOT NULL

        UNION ALL

        SELECT
            kb.id AS result_id,
            'kb_article'::TEXT AS result_type,
            kb.title AS title,
            kb.content AS content,
            1 - (kb.embedding <=> p_query_embedding) AS sem_score,
            COALESCE(ts_rank(kb.search_vector, plainto_tsquery('english', p_query_text)), 0) AS lex_score,
            (CASE WHEN p_error_code IS NOT NULL AND p_error_code = ANY(kb.error_codes) THEN 0.3 ELSE 0 END
             + CASE WHEN p_tcode IS NOT NULL AND p_tcode = ANY(kb.tcodes) THEN 0.2 ELSE 0 END) AS ex_boost
        FROM kb_articles kb
        WHERE kb.tenant_id = p_tenant_id
            AND kb.embedding IS NOT NULL
    )
    SELECT
        combined.result_id,
        combined.result_type,
        combined.title,
        combined.content,
        (0.4 * combined.sem_score + 0.3 * combined.lex_score + combined.ex_boost) AS final_score,
        combined.sem_score AS semantic_score,
        combined.lex_score AS lexical_score,
        combined.ex_boost AS exact_boost
    FROM combined
    WHERE (0.4 * combined.sem_score + 0.3 * combined.lex_score + combined.ex_boost) >= p_min_score
    ORDER BY (0.4 * combined.sem_score + 0.3 * combined.lex_score + combined.ex_boost) DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
""")

    # ------------------------------------------------------------------ #
    # search_vector trigger — tickets
    # ------------------------------------------------------------------ #
    op.execute("""
CREATE OR REPLACE FUNCTION update_ticket_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.error_code, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.tcode, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
""")
    op.execute("""
CREATE TRIGGER ticket_search_vector_trigger
    BEFORE INSERT OR UPDATE ON tickets
    FOR EACH ROW EXECUTE FUNCTION update_ticket_search_vector();
""")

    # ------------------------------------------------------------------ #
    # search_vector trigger — kb_articles
    # ------------------------------------------------------------------ #
    op.execute("""
CREATE OR REPLACE FUNCTION update_kb_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.content, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
""")
    op.execute("""
CREATE TRIGGER kb_search_vector_trigger
    BEFORE INSERT OR UPDATE ON kb_articles
    FOR EACH ROW EXECUTE FUNCTION update_kb_search_vector();
""")


def downgrade() -> None:
    # Triggers
    op.execute("DROP TRIGGER IF EXISTS kb_search_vector_trigger ON kb_articles")
    op.execute("DROP TRIGGER IF EXISTS ticket_search_vector_trigger ON tickets")

    # Functions
    op.execute("DROP FUNCTION IF EXISTS update_kb_search_vector()")
    op.execute("DROP FUNCTION IF EXISTS update_ticket_search_vector()")
    op.execute("DROP FUNCTION IF EXISTS hybrid_search(TEXT, vector, TEXT, TEXT, TEXT, TEXT, FLOAT, INT)")

    # Tables (reverse dependency order)
    op.drop_table("eval_golden_set")
    op.drop_table("model_versions")
    op.drop_table("kb_articles")
    op.drop_table("feedback")
    op.drop_table("triage_decisions")
    op.drop_table("tickets")
    op.drop_table("tenants")
