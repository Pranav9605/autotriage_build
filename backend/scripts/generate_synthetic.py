"""Generate 100 synthetic SAP support tickets for AutoTriage seeding and evaluation.

Outputs:
  scripts/data/synthetic_tickets.json  — all 100 tickets
  scripts/data/eval_holdout.json       — last 20 tickets (holdout set)

Run:
  python scripts/generate_synthetic.py
"""

import json
import random
from pathlib import Path

random.seed(42)

OUTPUT_DIR = Path(__file__).parent / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Indian name pool
# ---------------------------------------------------------------------------
FIRST_NAMES = [
    "Rahul", "Priya", "Amit", "Sunita", "Ravi", "Deepa", "Vijay", "Kavita",
    "Suresh", "Meena", "Anil", "Pooja", "Manoj", "Rekha", "Sanjay", "Lata",
    "Rajesh", "Neha", "Dinesh", "Asha", "Prakash", "Seema", "Naresh", "Usha",
    "Girish", "Nandini", "Hemant", "Pallavi", "Ajay", "Shreya", "Nitin",
    "Divya", "Sandeep", "Bhavna", "Ramesh", "Sudha", "Kishore", "Anita",
    "Vivek", "Smita",
]
LAST_NAMES = [
    "Patil", "Sharma", "Mehta", "Gupta", "Joshi", "Singh", "Rao", "Nair",
    "Iyer", "Desai", "Shah", "Verma", "Tiwari", "Chaudhari", "Kulkarni",
    "Mishra", "Pandey", "Reddy", "Kumar", "Malhotra",
]

def random_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

SOURCES = ["whatsapp", "email", "chat", "jira", "phone"]
ENVS = ["PRD"] * 60 + ["QAS"] * 25 + ["DEV"] * 15  # weighted

def random_source() -> str:
    return random.choice(SOURCES)

def random_env() -> str:
    return random.choice(ENVS)

# ---------------------------------------------------------------------------
# FI (Finance) — 30 tickets
# ---------------------------------------------------------------------------
FI_TICKETS = [
    # P1 — 4 tickets
    ("FB50 posting not working, getting F5 301 error in production. Year end closing is tomorrow. URGENT!", "P1", "PRD"),
    ("payment run F110 failed completely. All vendor payments stuck since 6am. Finance director is asking. Please help immediately", "P1", "PRD"),
    ("asset depreciation run failed AA 500 error in production. Month end closing in 2 hours cannot wait", "P1", "PRD"),
    ("entire FI module down. nobody can post any document since 9am. production system. please escalate", "P1", "PRD"),
    # P2 — 9 tickets
    ("MIRO invoice verification showing tax calculation error. Vendor Sharma Electronics bill for 5 lakh stuck. Already 3 days pending", "P2", "PRD"),
    ("f-02 manual journal entry not posting. error says posting period not open. closing is friday", "P2", "PRD"),
    ("FB60 vendor invoice posting giving dump. works in QAS but not in production. Strange", "P2", "PRD"),
    ("recurring entry FBD1 not generating for this month. accrual entries missing. auditors will ask", "P2", "PRD"),
    ("dunning run failed. customer statements not sent. accounts receivable team blocked", "P2", "PRD"),
    ("asset transfer ABUMN giving F5 702 error. need to move assets before quarter close", "P2", "PRD"),
    ("GR/IR clearing account showing huge open items. FK10N reconciliation not matching", "P2", "PRD"),
    ("bank reconciliation FF67 not posting. file uploaded but no entries coming", "P2", "PRD"),
    ("withholding tax certificate RFWT0010 report showing wrong amounts. compliance issue", "P2", "QAS"),
    # P3 — 12 tickets
    ("FB50 posting gives warning message about document type. posting works but warning confusing users", "P3", "PRD"),
    ("profit center assignment wrong on automatic posting. not urgent but needs fix", "P3", "QAS"),
    ("FBL1N vendor line item report very slow. taking 10 mins to load for old data", "P3", "PRD"),
    ("accounting team saying something wrong with journal entries cant post anything since 10am in quality system", "P3", "QAS"),
    ("cost center KS01 creation giving authorization error for some users. workaround is to use super user", "P3", "PRD"),
    ("FAGLL03 GL account line item display not showing correct balance. might be display issue", "P3", "PRD"),
    ("vendor payment terms not defaulting correctly on MIRO. user has to manually enter each time", "P3", "QAS"),
    ("currency revaluation FAGL_FC_VAL giving warning for some accounts. no hard error just concern", "P3", "DEV"),
    ("document splitting configuration not working for one company code. other company codes fine", "P3", "QAS"),
    ("intercompany posting IC01 not creating mirror entry in second company code automatically", "P3", "QAS"),
    ("tax code V1 in FB60 not calculating TDS correctly for one vendor category", "P3", "DEV"),
    ("FBL5N customer line items report not pulling closed items. filter issue maybe", "P3", "PRD"),
    # P4 — 5 tickets
    ("need new report showing vendor aging with payment terms. not urgent just enhancement", "P4", "DEV"),
    ("FB50 screen layout needs to show additional field for reference. customization request", "P4", "DEV"),
    ("payment advice email format needs logo and company address. cosmetic change only", "P4", "QAS"),
    ("FI document number range running low for current year. need to extend for next year planning", "P4", "PRD"),
    ("request to add custom field in vendor master for GST registration number. future requirement", "P4", "DEV"),
]

# ---------------------------------------------------------------------------
# BASIS (System/Infra) — 20 tickets
# ---------------------------------------------------------------------------
BASIS_TICKETS = [
    # P1 — 3 tickets
    ("production system completely down. ST22 showing ABAP_RUNTIME_ERROR every minute. all users locked out. CRITICAL", "P1", "PRD"),
    ("SAP not opening for anyone. SM21 showing memory overflow errors. business stopped", "P1", "PRD"),
    ("database tablespace full. system going into emergency mode. all operations halted", "P1", "PRD"),
    # P2 — 6 tickets
    ("SM50 showing 80 work processes all occupied. system very slow. users timing out", "P2", "PRD"),
    ("ST22 runtime dump TIME_OUT happening every 5 mins. background jobs failing. batch processing stopped", "P2", "PRD"),
    ("SM21 showing lot of errors. system performance very slow today everyone complaining since morning", "P2", "PRD"),
    ("background job RFFOUS_C for payment medium stuck since yesterday. Finance waiting for output", "P2", "PRD"),
    ("system gets slow after lunch when 50 plus users login simultaneously. response time unacceptable", "P2", "PRD"),
    ("STMS transport import failing with error. urgent config change stuck in queue", "P2", "QAS"),
    # P3 — 8 tickets
    ("SU01 user creation giving authorization error. new joiner cannot get access. IT team blocked", "P3", "PRD"),
    ("PFCG role modification not saving. need to update authorization for month end team", "P3", "PRD"),
    ("SM36 scheduled job not triggering at correct time. off by 30 mins. daylight saving issue maybe", "P3", "PRD"),
    ("STRUST certificate expiring next month. need to renew. not urgent but planned", "P3", "PRD"),
    ("SAP not opening for some users in Pune office. other offices fine. network or basis issue", "P3", "PRD"),
    ("client copy taking very long. been running 8 hours. should finish in 2 hours normally", "P3", "DEV"),
    ("SCOT email configuration not sending output. print preview works but email fails", "P3", "QAS"),
    ("SM12 lock entries piling up. users getting locked. need to clear old entries", "P3", "PRD"),
    # P4 — 3 tickets
    ("request to create new development client for upcoming project. planning activity", "P4", "DEV"),
    ("system monitoring dashboard CCMS showing yellow alerts. not critical but needs investigation", "P4", "PRD"),
    ("need to increase dialog work processes from 20 to 25. performance improvement request", "P4", "PRD"),
]

# ---------------------------------------------------------------------------
# MM (Materials Management) — 15 tickets
# ---------------------------------------------------------------------------
MM_TICKETS = [
    # P1 — 2 tickets
    ("ME21N purchase order creation completely failing M7 021 error. procurement blocked. vendor waiting", "P1", "PRD"),
    ("goods receipt not posting for any PO. MIGO throwing system error. warehouse operations stopped", "P1", "PRD"),
    # P2 — 5 tickets
    ("MB1A goods issue M8 108 error. production line waiting for material. 200 workers idle", "P2", "PRD"),
    ("PO approval workflow stuck for all purchase orders since yesterday evening. approvers not getting email", "P2", "PRD"),
    ("MIRO 3-way match failing. invoice amount matches PO but system not allowing posting. ME 573 error", "P2", "PRD"),
    ("inventory valuation CKMVFM giving error during period close. MM closing blocked", "P2", "PRD"),
    ("material master MM01 creation blocked. plant extension not saving. new product launch delayed", "P2", "QAS"),
    # P3 — 6 tickets
    ("MB52 stock report not matching physical count. small discrepancy. need reconciliation", "P3", "PRD"),
    ("purchasing info record ME11 price not updating from last PO. manual override needed each time", "P3", "PRD"),
    ("ME2N outstanding PO report very slow. filter by vendor taking 15 minutes", "P3", "PRD"),
    ("source list ME01 not restricting vendors properly. users able to select unapproved vendor", "P3", "QAS"),
    ("material movement type 101 posting but reservation not getting cleared automatically", "P3", "PRD"),
    ("batch management classification not assigning correctly on goods receipt. manual correction needed", "P3", "DEV"),
    # P4 — 2 tickets
    ("need custom report for slow-moving inventory. standard MB52 not sufficient. enhancement request", "P4", "DEV"),
    ("vendor evaluation ME61 scoring criteria needs update. process improvement request", "P4", "QAS"),
]

# ---------------------------------------------------------------------------
# SD (Sales & Distribution) — 15 tickets
# ---------------------------------------------------------------------------
SD_TICKETS = [
    # P1 — 2 tickets
    ("VF01 billing run completely stopped V1 801 error. cannot invoice any customer. revenue blocked", "P1", "PRD"),
    ("VA01 sales order not saving for any customer. system error. all sales operations stopped", "P1", "PRD"),
    # P2 — 5 tickets
    ("VL01N delivery creation blocked. ATP check failing for all orders. shipping team idle", "P2", "PRD"),
    ("customer credit block VKM3 not releasing. credit limit is fine in FD32 but still blocking. Sharma Steel order held for 2 days", "P2", "PRD"),
    ("pricing condition PR00 wrong in VA01. customer getting 15% less price than agreed. contract issue", "P2", "PRD"),
    ("billing output VF02 not sending to customer. EDI integration stopped. VN 008 error in message log", "P2", "PRD"),
    ("returns order RE01 not creating credit memo automatically. manual processing for 50 returns pending", "P2", "QAS"),
    # P3 — 6 tickets
    ("VA05 open order report not showing correct status. some orders showing open when already delivered", "P3", "PRD"),
    ("sales order VB01 - contract determination not picking correct contract for customer", "P3", "PRD"),
    ("VL02N delivery change not allowed. locked by another user but that user already logged out", "P3", "PRD"),
    ("customer master XD01 creation giving error on account group validation. new customer onboarding delayed", "P3", "QAS"),
    ("packing instruction in VL01N not defaulting. warehouse team has to manually enter each time", "P3", "PRD"),
    ("SD billing split happening when it should not. single delivery getting split into 2 invoices", "P3", "PRD"),
    # P4 — 2 tickets
    ("need customer-wise sales report with YTD comparison. current standard reports not sufficient", "P4", "DEV"),
    ("sales order form layout needs to include GST number field. regulatory requirement for future", "P4", "DEV"),
]

# ---------------------------------------------------------------------------
# PI/PO (Integration) — 10 tickets
# ---------------------------------------------------------------------------
PI_TICKETS = [
    # P1 — 2 tickets
    ("SXMB_MONI showing 500 failed IDocs. ClearTax GST integration completely stopped. compliance at risk", "P1", "PRD"),
    ("XIAdapter error on PI/PO system. No data flowing to any external system since last night. All integrations down", "P1", "PRD"),
    # P2 — 4 tickets
    ("IDoc processing failing IDOC_ERROR. 200 outbound messages queued. Tally integration stopped", "P2", "PRD"),
    ("SXI_MONITOR showing failed messages for bank integration. automatic payment reconciliation stopped", "P2", "PRD"),
    ("ORDERS05 IDOC to vendor portal failing since ECC upgrade. EDI orders not reaching suppliers", "P2", "QAS"),
    ("BizTalk adapter not connecting to PI system. middleware team says PI side issue. certificates maybe", "P2", "PRD"),
    # P3 — 3 tickets
    ("PI message reprocessing SXMB_MONI taking very long. 1000 messages in queue piling up", "P3", "PRD"),
    ("mapping error in interface Z_FI_BANK_STATEMENT. some fields not mapping correctly to target structure", "P3", "QAS"),
    ("proxy class in PI not updated after IDOC extension. need to regenerate proxy after segment change", "P3", "DEV"),
    # P4 — 1 ticket
    ("need new interface from SAP to CRM system for customer master sync. scoping activity only", "P4", "DEV"),
]

# ---------------------------------------------------------------------------
# ABAP (Custom Dev) — 10 tickets
# ---------------------------------------------------------------------------
ABAP_TICKETS = [
    # P1 — 2 tickets
    ("custom report ZFI_AGING crashing with SYNTAX_ERROR after transport to production. All FI reports down", "P1", "PRD"),
    ("ABAP dump in ZMMSTOCK_REPORT every time it runs. production users cannot get inventory data", "P1", "PRD"),
    # P2 — 3 tickets
    ("enhancement spot in VL01N throwing dump after EHP upgrade. delivery creation failing", "P2", "PRD"),
    ("custom BAPI Z_CREATE_VENDOR not returning correct data after last code change. mass vendor creation broken", "P2", "QAS"),
    ("user exit in ME21N not triggering since recent transport. custom validations skipped", "P2", "PRD"),
    # P3 — 4 tickets
    ("ABAP dump in ZMMREPORT after latest transport to QAS. error in new enhancement. DEV works fine", "P3", "QAS"),
    ("performance issue in custom report ZFBCUST. 50000 records taking 30 minutes. needs optimization", "P3", "PRD"),
    ("SE38 ABAP editor not allowing save for one developer. authorization or lock issue", "P3", "DEV"),
    ("custom smartform ZSD_INVOICE layout broken after print workbench change. minor cosmetic issue", "P3", "QAS"),
    # P4 — 1 ticket
    ("SE80 - need to create new Z-package for upcoming project. code organization request", "P4", "DEV"),
]

# ---------------------------------------------------------------------------
# Assemble all tickets
# ---------------------------------------------------------------------------
ALL_TICKET_SPECS = (
    [("FI", txt, pri, env) for txt, pri, env in FI_TICKETS]
    + [("BASIS", txt, pri, env) for txt, pri, env in BASIS_TICKETS]
    + [("MM", txt, pri, env) for txt, pri, env in MM_TICKETS]
    + [("SD", txt, pri, env) for txt, pri, env in SD_TICKETS]
    + [("PI_PO", txt, pri, env) for txt, pri, env in PI_TICKETS]
    + [("ABAP", txt, pri, env) for txt, pri, env in ABAP_TICKETS]
)

assert len(ALL_TICKET_SPECS) == 100, f"Expected 100 tickets, got {len(ALL_TICKET_SPECS)}"

random.shuffle(ALL_TICKET_SPECS)

tickets = []
for module, raw_text, priority, env in ALL_TICKET_SPECS:
    tickets.append({
        "source": random_source(),
        "raw_text": raw_text,
        "reporter": random_name(),
        "environment": env,
        "ground_truth_module": module,
        "ground_truth_priority": priority,
    })

working_set = tickets[:80]
holdout_set = tickets[80:]

OUTPUT_DIR.joinpath("synthetic_tickets.json").write_text(
    json.dumps(working_set, indent=2, ensure_ascii=False)
)
OUTPUT_DIR.joinpath("eval_holdout.json").write_text(
    json.dumps(holdout_set, indent=2, ensure_ascii=False)
)

# Summary
from collections import Counter
mod_counts = Counter(t["ground_truth_module"] for t in tickets)
pri_counts = Counter(t["ground_truth_priority"] for t in tickets)
src_counts = Counter(t["source"] for t in tickets)

print(f"Generated {len(tickets)} tickets:")
print(f"  Working set : {len(working_set)}")
print(f"  Holdout set : {len(holdout_set)}")
print(f"\nModule distribution: {dict(mod_counts)}")
print(f"Priority distribution: {dict(pri_counts)}")
print(f"Source distribution: {dict(src_counts)}")
print(f"\nSaved to: {OUTPUT_DIR}/")
