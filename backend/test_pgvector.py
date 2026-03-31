# smoke_test_pgvector.py
# Run this FIRST before deploying any schema.
# All 5 checks must pass before proceeding to Day 1 schema deployment.

import psycopg2
import numpy as np
import time

DB_URL = "postgresql://user:password@localhost:5432/autotriage"

def run(label, fn):
    try:
        fn()
        print(f"  ✅ {label}")
        return True
    except Exception as e:
        print(f"  ❌ {label} — {e}")
        return False

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()
results = []

print("\n── AutoTriage pgvector Smoke Test ──\n")

# CHECK 1: Extension installs cleanly
def check_extension():
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    conn.commit()

results.append(run("pgvector + pg_trgm extensions install", check_extension))

# CHECK 2: Table with 1536-dim vector column (text-embedding-3-small dimension)
def check_table():
    cur.execute("""
        CREATE TABLE IF NOT EXISTS _smoke_test (
            id SERIAL PRIMARY KEY,
            content TEXT,
            embedding vector(1536)
        );
    """)
    conn.commit()

results.append(run("Create table with vector(1536) column", check_table))

# CHECK 3: Insert 10 random vectors + text
def check_insert():
    for i in range(10):
        vec = np.random.rand(1536).tolist()
        cur.execute(
            "INSERT INTO _smoke_test (content, embedding) VALUES (%s, %s)",
            (f"test document {i}", str(vec))
        )
    conn.commit()

results.append(run("Insert 10 random 1536-dim vectors", check_insert))

# CHECK 4: IVFFlat index creation (same index type used in production)
def check_index():
    cur.execute("""
        CREATE INDEX IF NOT EXISTS _smoke_idx
        ON _smoke_test
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 5);
    """)
    conn.commit()

results.append(run("IVFFlat cosine index creation", check_index))

# CHECK 5: Cosine similarity query returns results + measures latency
def check_query():
    query_vec = np.random.rand(1536).tolist()
    start = time.perf_counter()
    cur.execute("""
        SELECT id, content, 1 - (embedding <=> %s::vector) AS score
        FROM _smoke_test
        ORDER BY embedding <=> %s::vector
        LIMIT 3;
    """, (str(query_vec), str(query_vec)))
    rows = cur.fetchall()
    latency = (time.perf_counter() - start) * 1000

    assert len(rows) == 3, f"Expected 3 results, got {len(rows)}"
    assert all(0.0 <= row[2] <= 1.0 for row in rows), "Scores out of [0, 1] range"
    print(f"       Latency: {latency:.2f}ms | Top score: {rows[0][2]:.4f}")

results.append(run("Cosine similarity query (top 3, with latency)", check_query))

# CLEANUP
cur.execute("DROP TABLE IF EXISTS _smoke_test;")
cur.execute("DROP INDEX IF EXISTS _smoke_idx;")
conn.commit()
cur.close()
conn.close()

# VERDICT
print(f"\n── Result: {sum(results)}/5 checks passed ──")
if all(results):
    print("✅ pgvector is ready. Proceed to schema deployment.\n")
else:
    print("❌ Fix failures above before running schema. Do NOT proceed.\n")
