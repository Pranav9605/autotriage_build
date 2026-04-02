"""
demo.py — Smoke-test and demo script for AutoTriage.

Demonstrates the full flow via live HTTP calls to a running server:
  1. Create 3 tickets (FI/easy, WhatsApp/vague, ABAP+PRD/critical)
  2. Print triage results for each
  3. Submit feedback (accept first, override second, accept third)
  4. Fetch dashboard KPIs and print them
  5. Search KB for "posting error" and print results

Prerequisites:
  uvicorn app.main:app --reload   (must be running on localhost:8000)
  Tenant config: config/patil_group.yaml must exist
"""

import json
import sys
import httpx

BASE_URL = "http://localhost:8000"
TENANT_ID = "patil_group"
HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-Id": TENANT_ID,
}

TICKETS = [
    {
        "label": "FI / Easy",
        "source": "solman",
        "raw_text": (
            "FB50 document posting is failing with error F5 301 in the production system. "
            "Month-end closing is blocked for company code 1000. "
            "Transaction code FB50. Error: F5 301 No amount entered."
        ),
        "reporter": "rahul.patil@patilgroup.com",
    },
    {
        "label": "WhatsApp / Vague",
        "source": "whatsapp",
        "raw_text": (
            "Hi, SAP is not working since morning. "
            "Cannot open my reports. Please help urgently."
        ),
        "reporter": "priya.sharma@patilgroup.com",
    },
    {
        "label": "ABAP + PRD / Critical",
        "source": "solman",
        "raw_text": (
            "ABAP runtime error SYNTAX_ERROR in program ZMONTHEND_CLOSE occurring in PRD system. "
            "SE38 shows syntax error after recent transport. "
            "Month-end closing completely blocked."
        ),
        "reporter": "dev.team@patilgroup.com",
    },
]


def _print_section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


def _print_triage(label: str, triage: dict) -> None:
    print(f"\n  [{label}]")
    print(f"    ticket_id  : {triage.get('ticket_id')}")
    print(f"    module     : {triage.get('module')}")
    print(f"    priority   : {triage.get('priority')}")
    print(f"    confidence : {triage.get('confidence', 0):.2f}")
    print(f"    assign_to  : {triage.get('assign_to')}")
    if triage.get("manual_review_required"):
        print(f"    ⚠ manual review: {triage.get('review_reason')}")
    if triage.get("rules_applied"):
        print(f"    rules      : {', '.join(triage['rules_applied'])}")


def main() -> None:
    client = httpx.Client(base_url=BASE_URL, headers=HEADERS, timeout=60.0)

    # ------------------------------------------------------------------
    # 1. Create 3 tickets
    # ------------------------------------------------------------------
    _print_section("STEP 1 — Creating 3 tickets")
    ticket_ids: list[str] = []
    decision_ids: list[str] = []

    for ticket_spec in TICKETS:
        label = ticket_spec["label"]
        payload = {
            "source": ticket_spec["source"],
            "raw_text": ticket_spec["raw_text"],
            "reporter": ticket_spec.get("reporter"),
        }
        resp = client.post("/api/v1/tickets", json=payload)
        if resp.status_code != 201:
            print(f"  ERROR creating [{label}]: {resp.status_code} — {resp.text}")
            sys.exit(1)

        body = resp.json()
        triage = body.get("triage") or {}
        ticket_ids.append(body["id"])
        decision_ids.append(triage.get("decision_id", ""))
        _print_triage(label, triage)

    # ------------------------------------------------------------------
    # 2. Submit feedback
    # ------------------------------------------------------------------
    _print_section("STEP 2 — Submitting feedback")

    feedback_payloads = [
        {
            "label": "Accept FI ticket",
            "decision_id": decision_ids[0],
            "body": {"action": "accepted", "consultant_id": "consultant-demo"},
        },
        {
            "label": "Override WhatsApp ticket (module → BASIS)",
            "decision_id": decision_ids[1],
            "body": {
                "action": "overridden",
                "overrides": {"module": "BASIS"},
                "override_category": "wrong_module",
                "comment": "User cannot log in — BASIS issue, not generic.",
                "consultant_id": "consultant-demo",
            },
        },
        {
            "label": "Accept ABAP ticket",
            "decision_id": decision_ids[2],
            "body": {"action": "accepted", "consultant_id": "consultant-demo"},
        },
    ]

    for fb in feedback_payloads:
        if not fb["decision_id"]:
            print(f"  SKIP [{fb['label']}] — no decision_id")
            continue
        resp = client.post(f"/api/v1/triage/{fb['decision_id']}/feedback", json=fb["body"])
        if resp.status_code not in (200, 201):
            print(f"  ERROR [{fb['label']}]: {resp.status_code} — {resp.text}")
        else:
            r = resp.json()
            print(f"  [{fb['label']}] → action={r['action']}  "
                  f"correct_module={r['is_correct_module']}  "
                  f"final_module={r['final_module']}")

    # ------------------------------------------------------------------
    # 3. Dashboard KPIs
    # ------------------------------------------------------------------
    _print_section("STEP 3 — Dashboard KPIs")
    resp = client.get("/api/v1/dashboard/kpis")
    if resp.status_code == 200:
        kpis = resp.json()
        print(f"  total_tickets    : {kpis['total_tickets']}")
        print(f"  triaged_tickets  : {kpis['triaged_tickets']}")
        print(f"  accuracy_rate    : {kpis['accuracy_rate']:.1%}")
        print(f"  override_rate    : {kpis['override_rate']:.1%}")
        print(f"  avg_confidence   : {kpis['avg_confidence']:.2f}")
        print(f"  avg_latency_ms   : {kpis['avg_latency_ms']:.0f} ms")
    else:
        print(f"  ERROR: {resp.status_code} — {resp.text}")

    # ------------------------------------------------------------------
    # 4. KB search
    # ------------------------------------------------------------------
    _print_section("STEP 4 — KB search: 'posting error'")
    resp = client.get("/api/v1/kb/search", params={"q": "posting error"})
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        if results:
            for r in results[:3]:
                print(f"  [{r['module']}] {r['title']}")
        else:
            print("  No KB articles found (run seed_db.py first)")
    else:
        print(f"  ERROR: {resp.status_code} — {resp.text}")

    _print_section("DEMO COMPLETE")
    print(f"\n  Created tickets  : {ticket_ids}")
    print(f"  Decision IDs     : {decision_ids}")
    print(f"\n  Swagger UI → http://localhost:8000/docs\n")


if __name__ == "__main__":
    main()
