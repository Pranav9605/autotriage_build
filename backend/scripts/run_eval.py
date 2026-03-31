"""Evaluation script — run holdout tickets through the API and measure accuracy.

Usage:
  python scripts/run_eval.py                     # Runs against http://localhost:8000
  python scripts/run_eval.py --api-url http://...
  python scripts/run_eval.py --tenant patil_group

Requirements:
  - AutoTriage server running (uvicorn app.main:app --reload)
  - Database seeded (python scripts/seed_db.py)
  - .env with ANTHROPIC_API_KEY and OPENAI_API_KEY
"""

import argparse
import asyncio
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import httpx

DATA_DIR = Path(__file__).parent / "data"


def load_holdout() -> list:
    path = DATA_DIR / "eval_holdout.json"
    if not path.exists():
        print("ERROR: eval_holdout.json not found. Run generate_synthetic.py first.")
        sys.exit(1)
    return json.loads(path.read_text())


async def run_eval(api_url: str, tenant_id: str) -> None:
    holdout = load_holdout()
    print(f"Running evaluation on {len(holdout)} holdout tickets...")
    print(f"API: {api_url}, Tenant: {tenant_id}\n")

    results = []
    headers = {"X-Tenant-Id": tenant_id, "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        for i, ticket in enumerate(holdout):
            try:
                resp = await client.post(
                    f"{api_url}/api/v1/tickets",
                    json={"source": ticket["source"], "raw_text": ticket["raw_text"],
                          "reporter": ticket.get("reporter")},
                    headers=headers,
                )
                if resp.status_code not in (200, 201):
                    print(f"  [{i+1}/{len(holdout)}] HTTP {resp.status_code}: {resp.text[:100]}")
                    results.append({
                        "ticket": ticket, "error": f"HTTP {resp.status_code}", "triage": None
                    })
                    continue

                triage_data = resp.json().get("triage", {})
                result = {
                    "ticket": ticket,
                    "error": None,
                    "triage": triage_data,
                    "pred_module": triage_data.get("module"),
                    "pred_priority": triage_data.get("priority"),
                    "true_module": ticket["ground_truth_module"],
                    "true_priority": ticket["ground_truth_priority"],
                    "confidence": triage_data.get("confidence", 0.0),
                    "module_correct": triage_data.get("module") == ticket["ground_truth_module"],
                    "priority_correct": triage_data.get("priority") == ticket["ground_truth_priority"],
                }
                results.append(result)
                status = "✓" if result["module_correct"] else "✗"
                print(f"  [{i+1:02d}/{len(holdout)}] {status} "
                      f"pred={result['pred_module']}/{result['pred_priority']} "
                      f"true={result['true_module']}/{result['true_priority']} "
                      f"conf={result['confidence']:.2f}")

            except httpx.ConnectError:
                print(f"\nERROR: Cannot connect to {api_url}. Is the server running?")
                sys.exit(1)
            except Exception as exc:
                print(f"  [{i+1}/{len(holdout)}] Error: {exc}")
                results.append({"ticket": ticket, "error": str(exc), "triage": None})

    # -------------------------------------------------------------------------
    # Compute metrics
    # -------------------------------------------------------------------------
    valid = [r for r in results if r.get("error") is None]
    if not valid:
        print("\nNo valid results to evaluate.")
        return

    n = len(valid)
    module_correct = sum(1 for r in valid if r["module_correct"])
    priority_correct = sum(1 for r in valid if r["priority_correct"])
    both_correct = sum(1 for r in valid if r["module_correct"] and r["priority_correct"])

    overall_module_acc = module_correct / n
    overall_priority_acc = priority_correct / n
    overall_acc = both_correct / n
    avg_conf = sum(r["confidence"] for r in valid) / n
    avg_conf_correct = (
        sum(r["confidence"] for r in valid if r["module_correct"]) / module_correct
        if module_correct > 0 else 0.0
    )
    avg_conf_wrong = (
        sum(r["confidence"] for r in valid if not r["module_correct"]) / (n - module_correct)
        if (n - module_correct) > 0 else 0.0
    )

    # Per-module accuracy
    module_stats: dict = defaultdict(lambda: {"total": 0, "correct": 0})
    for r in valid:
        m = r["true_module"]
        module_stats[m]["total"] += 1
        if r["module_correct"]:
            module_stats[m]["correct"] += 1

    # Confusion matrix (true → predicted)
    confusion: dict = defaultdict(Counter)
    for r in valid:
        confusion[r["true_module"]][r["pred_module"]] += 1

    # -------------------------------------------------------------------------
    # Print report
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("AUTOTRIAGE EVALUATION REPORT")
    print("=" * 60)
    print(f"\nTotal holdout tickets  : {len(holdout)}")
    print(f"Successfully evaluated : {n}")
    print(f"Errors                 : {len(holdout) - n}")
    print(f"\nOverall module accuracy  : {overall_module_acc:.1%} ({module_correct}/{n})")
    print(f"Overall priority accuracy: {overall_priority_acc:.1%} ({priority_correct}/{n})")
    print(f"Both correct             : {overall_acc:.1%} ({both_correct}/{n})")
    print(f"\nMean confidence (all)    : {avg_conf:.3f}")
    print(f"Mean confidence (correct): {avg_conf_correct:.3f}")
    print(f"Mean confidence (wrong)  : {avg_conf_wrong:.3f}")

    print("\n--- Per-Module Accuracy ---")
    print(f"{'Module':<10} {'Total':>6} {'Correct':>8} {'Accuracy':>10}")
    print("-" * 38)
    for module in sorted(module_stats.keys()):
        s = module_stats[module]
        acc = s["correct"] / s["total"] if s["total"] > 0 else 0.0
        print(f"{module:<10} {s['total']:>6} {s['correct']:>8} {acc:>9.1%}")

    print("\n--- Module Confusion Matrix (rows=true, cols=predicted) ---")
    all_modules = sorted(set(r["true_module"] for r in valid) | set(r["pred_module"] for r in valid if r["pred_module"]))
    header = f"{'True\\Pred':<10}" + "".join(f"{m:>8}" for m in all_modules)
    print(header)
    print("-" * len(header))
    for true_m in all_modules:
        row = f"{true_m:<10}"
        for pred_m in all_modules:
            count = confusion[true_m][pred_m]
            row += f"{count:>8}" if count > 0 else f"{'·':>8}"
        print(row)

    # -------------------------------------------------------------------------
    # Save results
    # -------------------------------------------------------------------------
    eval_results = {
        "summary": {
            "total": len(holdout),
            "evaluated": n,
            "errors": len(holdout) - n,
            "overall_module_accuracy": round(overall_module_acc, 4),
            "overall_priority_accuracy": round(overall_priority_acc, 4),
            "both_correct": round(overall_acc, 4),
            "avg_confidence": round(avg_conf, 4),
            "avg_confidence_correct": round(avg_conf_correct, 4),
            "avg_confidence_wrong": round(avg_conf_wrong, 4),
        },
        "per_module": {
            m: {
                "total": s["total"],
                "correct": s["correct"],
                "accuracy": round(s["correct"] / s["total"], 4) if s["total"] > 0 else 0.0,
            }
            for m, s in module_stats.items()
        },
        "raw_results": [
            {
                "true_module": r["true_module"],
                "true_priority": r["true_priority"],
                "pred_module": r.get("pred_module"),
                "pred_priority": r.get("pred_priority"),
                "confidence": r.get("confidence"),
                "module_correct": r.get("module_correct"),
                "priority_correct": r.get("priority_correct"),
            }
            for r in valid
        ],
    }

    out_path = DATA_DIR / "eval_results.json"
    out_path.write_text(json.dumps(eval_results, indent=2))
    print(f"\nResults saved to: {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AutoTriage evaluation")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--tenant", default="patil_group")
    args = parser.parse_args()

    asyncio.run(run_eval(api_url=args.api_url, tenant_id=args.tenant))
