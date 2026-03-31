"""Generate 30 SAP knowledge base articles for AutoTriage seeding.

Output: scripts/data/kb_articles.json

Run:
  python scripts/generate_kb_articles.py
"""

import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

KB_ARTICLES = [
    # -----------------------------------------------------------------------
    # FI — 10 articles
    # -----------------------------------------------------------------------
    {
        "title": "F5 301 Error: Posting Period Not Open in FI",
        "content": (
            "The F5 301 error ('Posting period X/YYYY is not open for account type S') occurs when a user "
            "attempts to post a document in SAP FI to a fiscal period that has not been opened or has already "
            "been closed. This is one of the most frequent errors during month-end and year-end close activities.\n\n"
            "Common causes: (1) The posting period variant has not been updated to include the current period. "
            "(2) The document date falls in a different period than the posting date. "
            "(3) The user is trying to post to a prior period that is closed for normal users but open for "
            "controllers.\n\n"
            "Resolution steps: (1) Go to transaction OB52 and check the posting period variants assigned to "
            "your company code. (2) Open the relevant period for account types S (GL), D (Customer), K (Vendor) "
            "as appropriate. (3) For controlled prior-period postings, set a specific user range in OB52. "
            "(4) After updating, test by posting the document again in FB50 or FB60. "
            "(5) If the issue persists, check if the fiscal year variant is correctly configured in OB29.\n\n"
            "Prevention: Establish a period-open checklist as part of month-end procedures. Consider using "
            "variant periods in OB52 to allow controllers extended access while restricting normal users."
        ),
        "module": "FI",
        "error_codes": ["F5 301"],
        "tcodes": ["OB52", "FB50", "FB60", "OB29"],
        "tags": ["posting-period", "period-close", "F5-301", "GL-posting"],
    },
    {
        "title": "F5 702 Error: Asset Transaction Blocked by Fiscal Year",
        "content": (
            "Error F5 702 appears during asset transactions (ABUMN, ABZE, ABAON) when the asset fiscal year "
            "has not been closed or when there is a mismatch between the asset accounting fiscal year and the "
            "general ledger fiscal year.\n\n"
            "Common causes: (1) Asset fiscal year close (AJAB) not yet run while GL is already in new year. "
            "(2) Depreciation run (AFAB) has not completed for the prior year. "
            "(3) Asset value date falls outside the open period for asset accounting.\n\n"
            "Resolution steps: (1) Check asset accounting fiscal year status via AJRW (fiscal year change). "
            "(2) Ensure all depreciation areas are balanced — run AFAB if pending. "
            "(3) Execute AJAB (fiscal year close for Asset Accounting) if GL close is complete. "
            "(4) Verify the asset value date is within an open period. "
            "(5) If this is an asset transfer under ABUMN, ensure both sender and receiver company codes have "
            "the same open fiscal year status.\n\n"
            "Important: Always run depreciation (AFAB) before attempting fiscal year close (AJAB). Skipping "
            "this sequence is the most common cause of F5 702 in production environments."
        ),
        "module": "FI",
        "error_codes": ["F5 702"],
        "tcodes": ["ABUMN", "AJAB", "AJRW", "AFAB", "ABAON"],
        "tags": ["asset-accounting", "fiscal-year-close", "depreciation", "F5-702"],
    },
    {
        "title": "AA 500 Error: Depreciation Run Failures in Asset Accounting",
        "content": (
            "AA 500 ('Error in depreciation posting') is a critical error that stops the periodic depreciation "
            "run (AFAB) from completing. This error blocks month-end close for the entire asset accounting module.\n\n"
            "Common causes: (1) Asset master data inconsistencies — missing depreciation key or useful life. "
            "(2) GL account for depreciation expense not found or blocked. "
            "(3) Accumulated depreciation exceeds the asset's acquisition value (over-depreciation). "
            "(4) FI posting period closed while depreciation run is in progress.\n\n"
            "Resolution steps: (1) Run AFAB in 'Test Run' mode first to identify all error assets. "
            "(2) Check error log via SM37 → select the background job → display log. "
            "(3) For each error asset, go to AS02 and verify depreciation areas: check start date, useful life, "
            "and depreciation key (AW01N for asset explorer). "
            "(4) For GL account errors, verify account determination in AO90. "
            "(5) After fixing individual assets, restart AFAB with 'Repeat' run for the affected period. "
            "(6) For over-depreciation, use ABSO to post a manual write-up.\n\n"
            "Escalation note: If more than 10% of assets have errors, involve the Asset Accounting consultant "
            "— this may indicate a systematic configuration issue rather than individual data problems."
        ),
        "module": "FI",
        "error_codes": ["AA 500"],
        "tcodes": ["AFAB", "AS02", "AW01N", "AO90", "ABSO", "SM37"],
        "tags": ["depreciation", "asset-accounting", "AA-500", "month-end"],
    },
    {
        "title": "Payment Run F110: Troubleshooting Stuck or Failed Payment Runs",
        "content": (
            "Transaction F110 (Automatic Payment Program) handles bulk vendor and customer payments in SAP FI. "
            "When a payment run fails or gets stuck, it can block all outgoing payments and disrupt vendor "
            "relationships. Symptoms: Run stays in 'Payment proposal created' status, no payment document "
            "posted, or payment medium file not generated.\n\n"
            "Common causes: (1) Vendor bank details missing or incorrectly configured. "
            "(2) House bank or payment method not assigned to company code. "
            "(3) Posting period closed during run execution. "
            "(4) Log file area full — especially in high-volume runs. "
            "(5) Process terminated abnormally (power outage, system error) leaving a lock.\n\n"
            "Resolution steps: (1) Check run log in F110 → Printout/data medium tab. "
            "(2) For stuck runs: check SM12 for lock entries on the F110 run ID and clear if stale. "
            "(3) Verify house bank configuration: FBZP → House Banks → check GL account assignment. "
            "(4) For missing bank details, update vendor master FK02 → Payment transactions tab. "
            "(5) If run is stuck in 'Payment run active' status: wait 10 minutes, then delete via F110 → "
            "Edit → Delete run. Recreate the run parameters.\n\n"
            "Recovery: After fixing root cause, always start from 'Proposal' step again — do not attempt "
            "to continue a partially failed run as it may cause duplicate payments."
        ),
        "module": "FI",
        "error_codes": [],
        "tcodes": ["F110", "FBZP", "FK02", "SM12"],
        "tags": ["payment-run", "F110", "vendor-payment", "house-bank"],
    },
    {
        "title": "MIRO Invoice Verification: Tax Calculation Errors and 3-Way Match Failures",
        "content": (
            "Transaction MIRO (Enter Incoming Invoice) is used for vendor invoice processing against purchase "
            "orders. Common errors include tax calculation discrepancies, 3-way match failures (PO-GR-Invoice "
            "mismatch), and tolerance limit exceeded messages.\n\n"
            "For tax calculation errors: (1) Verify the tax code assigned on the PO line matches the vendor's "
            "GST/tax category. (2) Check FTXP for correct tax rates on the tax code. "
            "(3) Verify vendor master (XK02) → Accounting → Tax information section. "
            "(4) For TDS/WHT issues, check QBEW and the withholding tax type configuration.\n\n"
            "For 3-way match failures: (1) Compare PO quantity (ME23N) vs GR quantity (MB03) vs invoice. "
            "(2) Check tolerance limits in MM OMR6 — invoice value vs PO price tolerance. "
            "(3) For price variance: If within tolerance, post and send for approval. If outside, request "
            "price amendment from vendor before posting.\n\n"
            "For blocked invoices after MIRO: Use MRBR to review and release blocked invoices. "
            "Finance manager approval may be required for price variances above defined thresholds.\n\n"
            "GST-specific note for India: Ensure HSN/SAC codes are correctly maintained on PO lines and "
            "that the GSTIN of the vendor is validated before posting. Incorrect GST can create compliance "
            "issues during GSTR-2A reconciliation."
        ),
        "module": "FI",
        "error_codes": [],
        "tcodes": ["MIRO", "MRBR", "FTXP", "XK02", "ME23N", "MB03", "OMR6"],
        "tags": ["invoice-verification", "MIRO", "3-way-match", "tax", "GST"],
    },
    {
        "title": "GL Account Posting Errors: Document Type and Field Status Issues",
        "content": (
            "Posting errors in FB50 (Enter G/L Account Document) and related transactions often relate to "
            "field status group configuration, document type restrictions, or account type mismatches.\n\n"
            "Field status errors ('Field XXXXX is required' or 'Field XXXXX must not be filled'): "
            "(1) Check the field status group on the GL account master (FS00). "
            "(2) Cross-reference with posting key field status (OB41) and company code field status (OBC4). "
            "The stricter setting wins. "
            "(3) If a required field is missing, update the document or add default values.\n\n"
            "Document type issues: (1) Verify document type configuration in OBA7. "
            "(2) Ensure the account types allowed for the document type match the accounts being posted. "
            "(3) Check number range assignment for the document type.\n\n"
            "Substitution/validation errors: If a custom substitution or validation (GGB1/GGB0) is triggering, "
            "review the rule and ensure the business condition is correctly defined.\n\n"
            "Park and Post workflow: For users who cannot resolve blocking errors immediately, use FBV1 to "
            "park the document, then have an authorized user complete it in FBV2."
        ),
        "module": "FI",
        "error_codes": [],
        "tcodes": ["FB50", "FS00", "OB41", "OBC4", "OBA7", "GGB1", "GGB0", "FBV1", "FBV2"],
        "tags": ["GL-posting", "field-status", "document-type", "FB50"],
    },
    {
        "title": "Fiscal Year End Closing Checklist for SAP FI",
        "content": (
            "Year-end closing in SAP FI requires a precise sequence of activities. Doing them out of order "
            "causes cascading errors including F5 301, F5 702, and AA 500.\n\n"
            "Recommended closing sequence: (1) Complete all open items: clear GR/IR accounts (F.13), "
            "clear open items (F-32 for customers, F-44 for vendors). "
            "(2) Run final depreciation for the year (AFAB — posting run, not test). "
            "(3) Run year-end asset accounting close (AJAB). "
            "(4) Close prior period for normal postings in OB52 (keep open for controllers). "
            "(5) Run GR/IR clearing (F.19). "
            "(6) Run GL reclassification if applicable (F101). "
            "(7) Open new fiscal year in OB52 for all account types. "
            "(8) Run AJRW (asset fiscal year change) to open new year for asset accounting. "
            "(9) Post any year-end accruals via FBD1 (recurring entries) or FB50. "
            "(10) Extract balance carry forward for GL (F.16), customers (F.07), vendors (F.07).\n\n"
            "Common mistakes: Running AJAB before AFAB, forgetting to open the new period in OB52, "
            "and posting documents without checking the posting date falls in the new fiscal year.\n\n"
            "India-specific: Ensure all TDS certificates are generated (J1INCERT) before year-end. "
            "GSTR-3B reconciliation should be complete before closing the last period."
        ),
        "module": "FI",
        "error_codes": [],
        "tcodes": ["F.13", "F-32", "F-44", "AFAB", "AJAB", "OB52", "F.19", "F101", "AJRW", "F.16"],
        "tags": ["year-end-close", "fiscal-year", "closing-checklist", "best-practice"],
    },
    {
        "title": "Bank Reconciliation FF67: Uploading Electronic Bank Statements",
        "content": (
            "Transaction FF67 is used to upload and post electronic bank statements (MT940, BAI2, CAMT.053) "
            "in SAP FI. Failures here block daily bank reconciliation and cash position reporting.\n\n"
            "Common upload failures: (1) File format mismatch — verify the file format code in FEBAN "
            "matches the bank's actual output format. (2) House bank / account ID not found — verify "
            "configuration in FI12. (3) Business transaction code not mapped — check OBWW for mapping "
            "of bank transaction codes to SAP posting rules.\n\n"
            "Posting failures after successful upload: (1) Check FEBP (post electronic bank statement) for "
            "unprocessed line items. (2) Verify opening balance matches — balance discrepancies prevent posting. "
            "(3) For unmatched items, use FEBAN to manually assign open items or post to clearing accounts.\n\n"
            "For recurring 'No data found' message: Verify the statement date — SAP will not accept "
            "backdated statements if the period is closed. Also check if the file was already uploaded "
            "(duplicate statement prevention).\n\n"
            "Workaround for urgent situations: If FF67 continues to fail, use F-06 (manual bank posting) "
            "or FB05 to manually post the bank entries and clear open items. This should be a temporary "
            "measure only."
        ),
        "module": "FI",
        "error_codes": [],
        "tcodes": ["FF67", "FEBAN", "FEBP", "FI12", "OBWW", "F-06", "FB05"],
        "tags": ["bank-reconciliation", "FF67", "electronic-bank-statement", "house-bank"],
    },
    {
        "title": "Intercompany Postings: Configuration and Troubleshooting",
        "content": (
            "Intercompany postings in SAP FI automate the creation of mirror entries across company codes. "
            "When this breaks, intercompany receivables and payables go unbalanced, causing reconciliation "
            "problems at consolidation.\n\n"
            "Prerequisites: (1) Intercompany clearing accounts must be defined in OBYA for each company "
            "code pair. (2) Document types must allow cross-company posting (OBA7 → 'Intercompany postings' "
            "checkbox). (3) The trading partner field must be maintained on company code level.\n\n"
            "Common error: 'No intercompany posting account defined': (1) Go to OBYA. "
            "(2) Add the missing company code pair with the appropriate clearing account numbers. "
            "(3) Ensure both directions are configured (Company A → B and B → A).\n\n"
            "Document splitting issues: If New GL with document splitting is active, ensure the "
            "intercompany clearing account is assigned to a profit center. Missing profit center "
            "assignment is a frequent cause of document splitting errors on intercompany transactions.\n\n"
            "For automated intercompany billing, check the intercompany reconciliation settings in "
            "FBICR1 and ensure the reconciliation ledger is active."
        ),
        "module": "FI",
        "error_codes": [],
        "tcodes": ["OBYA", "OBA7", "FBICR1", "FB50"],
        "tags": ["intercompany", "cross-company", "clearing-account", "reconciliation"],
    },
    {
        "title": "Withholding Tax (TDS) Configuration and Posting Issues",
        "content": (
            "Withholding Tax (TDS/WHT) in SAP India is configured under the extended withholding tax "
            "framework. Incorrect TDS postings can cause compliance issues with Form 26AS reconciliation.\n\n"
            "Setup verification: (1) Check withholding tax type and code in SPRO → Financial Accounting → "
            "Financial Accounting Global Settings → Withholding Tax → Extended Withholding Tax. "
            "(2) Verify vendor master (XK02 → Withholding Tax tab) — all applicable WHT codes should be "
            "assigned with correct PAN details. (3) Check the WHT GL accounts in transaction OBC4/OB40.\n\n"
            "Common issue — TDS not deducting: (1) Verify that WHT is activated for the company code "
            "(SPRO → WHT → Company Code). (2) Check the minimum amount threshold configuration — "
            "TDS doesn't trigger below the threshold. (3) Verify invoice amount (not just line item) is "
            "above threshold.\n\n"
            "Certificate generation (J1INCERT): Ensure J1INQEFILE is run to consolidate challans before "
            "generating certificates. For quarterly return preparation, use J1INQFILE.\n\n"
            "Correcting wrong TDS postings: Use J1INREV to reverse and repost TDS entries. "
            "Do NOT manually adjust GL entries as this will break the WHT reporting tables."
        ),
        "module": "FI",
        "error_codes": [],
        "tcodes": ["XK02", "J1INCERT", "J1INQEFILE", "J1INREV", "J1INQFILE"],
        "tags": ["TDS", "withholding-tax", "India-compliance", "GST", "vendor"],
    },

    # -----------------------------------------------------------------------
    # BASIS — 6 articles
    # -----------------------------------------------------------------------
    {
        "title": "ABAP_RUNTIME_ERROR Dump Analysis and Resolution",
        "content": (
            "ABAP runtime dumps (ST22) indicate a program termination due to unhandled exceptions, memory "
            "errors, or programming defects. In production, recurring dumps of the same type indicate a "
            "systemic issue requiring immediate attention.\n\n"
            "Dump analysis steps: (1) Open ST22, select the dump and click 'Analyze'. "
            "(2) Review the 'Short description' (the error category) and 'What happened' section. "
            "(3) Check 'How to correct the error' for SAP's recommendation. "
            "(4) Note the program name and include — this identifies whether it's a standard or custom object.\n\n"
            "Common dump types and fixes: "
            "ABAP_RUNTIME_ERROR (memory overflow): Increase work process memory via rdisp/max_wprun_time "
            "and abap/heap_area_total. Check if a specific report is consuming excessive memory. "
            "TIME_OUT: Increase rdisp/max_wprun_time for the specific task type in RZ10. Consider "
            "optimizing the report using secondary indexes or SELECT additions. "
            "MESSAGE_TYPE_X: Custom validation throwing type-X message — locate the RAISE EXCEPTION in "
            "the code and add proper error handling.\n\n"
            "For custom code dumps: Involve ABAP developer to fix the root cause. ST22 provides the "
            "exact line number causing the dump. Use SAP Note search (notes.sap.com) with the dump "
            "exception class and program name for known fixes."
        ),
        "module": "BASIS",
        "error_codes": ["ABAP_RUNTIME_ERROR", "TIME_OUT"],
        "tcodes": ["ST22", "RZ10", "SM21"],
        "tags": ["dump", "ABAP-runtime", "performance", "ST22", "BASIS"],
    },
    {
        "title": "SM50/SM66 Work Process Monitoring and Performance Issues",
        "content": (
            "SM50 (Work Process Overview — local) and SM66 (Global Work Process Overview) are the primary "
            "tools for diagnosing SAP system performance issues. When all work processes are occupied, "
            "new user requests queue and the system appears 'frozen'.\n\n"
            "Reading SM50: (1) Sort by 'Time' column — processes running for >300 seconds are problematic. "
            "(2) Status 'Running' with high time = long-running process. "
            "(3) Status 'Stopped' = process waiting for a lock or external resource. "
            "(4) Type 'BTC' = background process; 'DIA' = dialog; 'UPD' = update.\n\n"
            "Immediate relief actions: (1) Identify user/program causing the bottleneck via the 'User' "
            "and 'Action' columns. (2) Contact the user if interactive — they may be able to cancel. "
            "(3) For runaway background jobs: SM37 → cancel the job. "
            "(4) For stuck UPDATE processes: SM13 to check and deactivate update requests blocking others.\n\n"
            "Root cause investigation: (1) Check SM21 for system log errors correlating to the slow period. "
            "(2) Use DB02 to check for table locks or long-running SQL. "
            "(3) Run ST05 (SQL trace) on a representative transaction to identify slow queries.\n\n"
            "Preventive measures: Set up CCMS alerts (RZ20) to notify BASIS team when work process "
            "utilization exceeds 80% for >5 minutes."
        ),
        "module": "BASIS",
        "error_codes": [],
        "tcodes": ["SM50", "SM66", "SM37", "SM13", "SM21", "DB02", "ST05", "RZ20"],
        "tags": ["performance", "work-process", "SM50", "BASIS", "monitoring"],
    },
    {
        "title": "STMS Transport Management: Import Failures and Queue Management",
        "content": (
            "STMS (Transport Management System) manages the movement of configuration and custom code "
            "between SAP system landscapes (DEV → QAS → PRD). Import failures here block critical changes "
            "from reaching production.\n\n"
            "Common import error categories: (1) Object already active in target: transport is trying to "
            "import an object that was modified directly in the target. Check if unauthorized direct changes "
            "were made. (2) Syntax error in transported code: review SE80 in the target system for the "
            "imported object. (3) Table structure mismatch: the transport includes a table change but the "
            "table data needs migration — check SPDD/SPAU after import.\n\n"
            "Import failure resolution: (1) In STMS on the target system, go to the import queue. "
            "(2) Double-click the failed transport to see the detailed log. "
            "(3) For each RC (return code): RC0=success, RC4=warning, RC8=error, RC12=critical error. "
            "(4) For RC8+: do not proceed to next transport until this is resolved — dependent transports "
            "will also fail. (5) For syntax errors: fix in DEV, create new transport, import.\n\n"
            "Emergency: If a critical fix transport is blocked by a failing unrelated transport, consult "
            "the transport coordinator — it may be possible to import specific transports out of sequence "
            "in exceptional circumstances (requires BASIS authorization and change management approval)."
        ),
        "module": "BASIS",
        "error_codes": [],
        "tcodes": ["STMS", "SE80", "SPDD", "SPAU", "SM37"],
        "tags": ["transport", "STMS", "change-management", "import", "BASIS"],
    },
    {
        "title": "SU01 / PFCG: User Authorization and Role Management",
        "content": (
            "Authorization management in SAP involves user master records (SU01), roles (PFCG), and "
            "authorization objects. 'Not authorized' errors (SY-SUBRC = 4 after AUTHORITY-CHECK) require "
            "systematic investigation rather than granting broad access.\n\n"
            "Diagnosing authorization failures: (1) Reproduce the error and immediately run SU53 to "
            "capture the authorization check that failed. This shows exactly which object and field "
            "values are missing. (2) Alternatively, activate user trace in ST01 (system trace) before "
            "reproducing the error for comprehensive analysis.\n\n"
            "Fixing missing authorizations: (1) Open the user's role in PFCG → Authorizations tab. "
            "(2) Use 'Change Authorization Data' → find the relevant authorization object. "
            "(3) Add the missing values (be precise — do not use '*' wildcards in production unless "
            "absolutely necessary). (4) Generate the profile and activate. "
            "(5) Use role transport (SCC1 or STMS) to move role changes to production.\n\n"
            "User unlock: For locked users (SU01 → 'User is locked' status): check if locked due to "
            "failed logon attempts (can be unlocked by BASIS) vs. locked by admin (requires approval). "
            "SU10 for mass user actions.\n\n"
            "Security note: Never grant SAP_ALL or SAP_NEW in production. Always follow least-privilege "
            "principle. Document all access changes with business justification."
        ),
        "module": "BASIS",
        "error_codes": [],
        "tcodes": ["SU01", "PFCG", "SU53", "ST01", "SU10"],
        "tags": ["authorization", "user-access", "PFCG", "SU01", "security"],
    },
    {
        "title": "Background Job Management: SM36, SM37 and Batch Processing",
        "content": (
            "Background jobs (batch processing) handle scheduled tasks like payment runs, reports, and "
            "period-end activities. Job failures or delays directly impact business processes.\n\n"
            "Job monitoring in SM37: (1) Filter by: Job Name (use wildcards like Z*), User, Status. "
            "(2) Status meanings: Active=running, Finished=completed, Released=scheduled waiting, "
            "Ready=ready to run, Interrupted=cancelled, Aborted=failed with error. "
            "(3) For failed jobs: select job → Job Log to see the error message.\n\n"
            "Common failure causes: (1) User behind the job is locked or password expired — check SU01. "
            "(2) Print spool overflow — clean up SP01 old spools. "
            "(3) Target server overloaded — in SM37, check the 'Target host' column. "
            "(4) Prerequisites not met — check if the job has a 'predecessor job' that failed.\n\n"
            "Job scheduling in SM36: (1) Always use a technical user (not a person's account) for "
            "job scheduling. Personal accounts expire and break scheduled jobs. "
            "(2) Set up CCMS alerts in RZ20 for critical jobs to notify on failure. "
            "(3) Use SM36 → 'After job' trigger for dependent job chains.\n\n"
            "For long-running jobs: Use SM50 to check work process status. If a job is in an infinite "
            "loop, cancel via SM37. For large data processing jobs, consider running in parallel "
            "using application-level job splitting."
        ),
        "module": "BASIS",
        "error_codes": [],
        "tcodes": ["SM36", "SM37", "SM50", "SP01", "SU01", "RZ20"],
        "tags": ["background-job", "batch-processing", "SM37", "scheduling", "BASIS"],
    },
    {
        "title": "SAP System Performance Tuning: Response Time and Memory",
        "content": (
            "System-wide performance degradation affects all users and can be caused by database, "
            "application server, or network bottlenecks. Systematic diagnosis before tuning is essential.\n\n"
            "Workload analysis with ST05 and SM66: Start with SM66 to see current active sessions and "
            "identify any obvious long-runners. Then use ST12 (ABAP trace) or ST05 (SQL trace) on "
            "representative slow transactions to identify the bottleneck layer (ABAP runtime vs. DB).\n\n"
            "Database performance: (1) Use DB02 to check table sizes and growth. Large, unindexed tables "
            "are frequent culprits. (2) DB05 for database statistics. (3) For PostgreSQL/HANA, check slow "
            "query logs directly. (4) Ensure statistics are up to date — outdated statistics cause poor "
            "query plans.\n\n"
            "Memory tuning: (1) RZ10 → Profile maintenance to adjust memory parameters. "
            "Key parameters: abap/heap_area_total (extended memory), rdisp/wp_no_dia (dialog processes). "
            "(2) Changes require system restart — plan during maintenance window.\n\n"
            "Quick wins: (1) Schedule SPAD (spool administration) cleanup for old spools. "
            "(2) Archive old data using SARA if tables like BSEG, MSEG are excessively large. "
            "(3) Restrict concurrent background jobs during peak dialog usage hours."
        ),
        "module": "BASIS",
        "error_codes": ["TIME_OUT"],
        "tcodes": ["ST05", "SM66", "ST12", "DB02", "DB05", "RZ10", "SPAD", "SARA"],
        "tags": ["performance", "tuning", "memory", "database", "BASIS"],
    },

    # -----------------------------------------------------------------------
    # MM — 5 articles
    # -----------------------------------------------------------------------
    {
        "title": "M7 021 Error: Goods Receipt and Inventory Posting Issues",
        "content": (
            "Error M7 021 ('Quantity in unit of entry exceeds quantity limit') occurs during goods "
            "receipts in MIGO or MB01 when the GR quantity exceeds the ordered or tolerated quantity "
            "on the purchase order.\n\n"
            "Immediate checks: (1) Compare the GR quantity with the outstanding PO quantity in ME23N. "
            "(2) Check the over-delivery tolerance on the PO line (ME23N → Item Details → Delivery tab). "
            "(3) If tolerance is 0%, even 1 extra unit triggers this error.\n\n"
            "Resolution options: (1) Adjust the GR quantity to match the PO outstanding quantity. "
            "(2) Increase the over-delivery tolerance on the PO (ME22N → Item → Delivery tab). "
            "This requires appropriate authorization and may need approver sign-off. "
            "(3) If extra quantity is valid, create a supplementary PO line for the difference. "
            "(4) For consignment stock, use movement type 101K instead of 101.\n\n"
            "Preventing future occurrences: Set standard over-delivery tolerances in the vendor master "
            "(XK02 → Purchasing Data → Over-delivery tolerance). Negotiate tolerance percentages with "
            "key vendors upfront and configure them in SAP material info records (ME12)."
        ),
        "module": "MM",
        "error_codes": ["M7 021"],
        "tcodes": ["MIGO", "ME23N", "ME22N", "XK02", "ME12"],
        "tags": ["goods-receipt", "M7-021", "over-delivery", "purchase-order", "MM"],
    },
    {
        "title": "M8 108 Error: Invoice Price Variance Beyond Tolerance",
        "content": (
            "Error M8 108 appears in MIRO when the invoice price differs from the purchase order price "
            "beyond the configured tolerance limit. This prevents automatic posting and requires either "
            "correction or manual approval.\n\n"
            "Understanding tolerances: Tolerance limits are configured in OMR6 (Invoice Verification "
            "tolerances). Key tolerance keys: BD (form small differences), BR (percentage, upper limit), "
            "BS (amount, upper limit), ST (date variance for payment terms).\n\n"
            "Resolution steps: (1) In MIRO, check the 'Balance' field — the difference amount is shown. "
            "(2) If variance is small and acceptable: post anyway if within absolute tolerance, system "
            "will post to price difference account automatically. "
            "(3) For significant variances: contact vendor for credit note or revised invoice. "
            "(4) If PO price was entered incorrectly, amend via ME22N (purchase order change) before "
            "re-posting the invoice. "
            "(5) Use MRBR to manage invoices blocked for payment due to price variance — they can be "
            "reviewed and released here with appropriate authorization.\n\n"
            "Accounting impact: Price variances are posted to PRD (Price Difference) accounts "
            "in moving average price valuation. Repeated variances indicate issues with PO pricing "
            "process that should be addressed at source."
        ),
        "module": "MM",
        "error_codes": ["M8 108"],
        "tcodes": ["MIRO", "OMR6", "ME22N", "MRBR", "MB03"],
        "tags": ["invoice-verification", "M8-108", "price-variance", "tolerance", "MM"],
    },
    {
        "title": "ME 573 Error: Purchase Order Approval Workflow Issues",
        "content": (
            "Error ME 573 ('Release strategy for purchase order not found') appears when the PO amount "
            "or category requires approval but no matching release strategy is configured for the "
            "combination of purchase organization, document type, and value.\n\n"
            "Diagnosis: (1) Check release strategy configuration: SPRO → MM → Purchasing → PO → "
            "Release Procedure → Define Release Procedure for Purchase Orders. "
            "(2) The release strategy is determined by characteristics: value, purchase org, plant, "
            "material group, document type. (3) Check if the PO falls within defined strategy ranges.\n\n"
            "Common causes: (1) PO value exceeds the highest configured threshold — no strategy "
            "handles values above that amount. (2) New plant or purchase org added without updating "
            "release strategies. (3) Classification characteristic value not maintained on PO.\n\n"
            "For stuck approvals (workflow not triggering email): (1) Check workflow status in SWIA. "
            "(2) Verify approver user exists in SU01 and has valid email in SU3. "
            "(3) For email delivery issues, check SCOT configuration.\n\n"
            "Emergency release: If business is blocked and configuration fix will take time, an authorized "
            "user with ME28 access can perform a manual release. This should be documented and exception "
            "approved by the purchasing manager."
        ),
        "module": "MM",
        "error_codes": ["ME 573"],
        "tcodes": ["ME21N", "ME28", "SWIA", "SCOT", "SU01"],
        "tags": ["purchase-order", "approval-workflow", "ME-573", "release-strategy", "MM"],
    },
    {
        "title": "MB51/MB52 Stock Discrepancy Analysis and Physical Inventory",
        "content": (
            "Stock discrepancies between SAP book stock and physical count are common in warehouses "
            "and require systematic reconciliation to maintain inventory accuracy.\n\n"
            "Analysis tools: (1) MB52 (Warehouse Stocks of Material) shows current book stock. "
            "(2) MB51 (Material Document List) shows all movements — use to trace when discrepancy occurred. "
            "(3) For date-range analysis, compare opening + receipts - issues = closing balance.\n\n"
            "Physical inventory process: (1) Create physical inventory document: MI01 (single storage "
            "location) or MICN (cycle counting). (2) Freeze book inventory: MI20 (print list), "
            "set 'Posting Block' on inventory document. (3) Enter count results: MI04 or MI08. "
            "(4) Differences report: MI20. (5) Post count differences: MI07 (after management approval "
            "for significant variances). Movement type 701 is used for inventory difference posting.\n\n"
            "Common causes of discrepancies: (1) Goods receipt posted but physical receipt not yet done. "
            "(2) Return deliveries not posted in SAP. (3) Scrapping not posted (MB1A, movement 551). "
            "(4) Transfer order not confirmed in WM (LT0A).\n\n"
            "For WM-managed storage locations: differences may exist between IM (inventory management) "
            "and WM (warehouse management) quantities. Use LX16 to list WM stock differences."
        ),
        "module": "MM",
        "error_codes": [],
        "tcodes": ["MB52", "MB51", "MI01", "MI04", "MI07", "MI20", "MB1A", "LX16"],
        "tags": ["inventory", "physical-inventory", "stock-reconciliation", "MB52", "MM"],
    },
    {
        "title": "Purchase Order Workflow and Approval Escalation Procedures",
        "content": (
            "Purchase order approval workflows in SAP MM ensure that spending commitments receive "
            "appropriate authorization before execution. When workflows fail or approvals are delayed, "
            "procurement operations can stall.\n\n"
            "Workflow monitoring: (1) Business Workplace (SBWP) — approvers see pending tasks here. "
            "(2) SWIA — administrators can see all workflow instances, reassign tasks, and restart failed "
            "workflows. (3) SWI5 — workload analysis by user to identify bottlenecked approvers.\n\n"
            "Substitution for absent approvers: (1) Use SWIA → find the work item → 'Forward' to "
            "substitute approver. (2) Or use SBWP → Settings → Maintain substitutes to set up "
            "automatic forwarding for a user's absence period.\n\n"
            "Release (approval) in SAP: (1) ME28 for collective release (approver can see all POs pending "
            "for their approval). (2) ME29N for individual PO release. "
            "(3) After release, verify PO status changes from 'Blocked' to no release strategy indicator.\n\n"
            "Escalation procedure: If an approver is unavailable and business impact is high: "
            "(1) Document the exception. (2) Get written approval from approver's manager. "
            "(3) Use ME28 with appropriate super-user access. (4) Record in change management system."
        ),
        "module": "MM",
        "error_codes": [],
        "tcodes": ["ME28", "ME29N", "SBWP", "SWIA", "SWI5"],
        "tags": ["purchase-order", "approval", "workflow", "release", "MM"],
    },

    # -----------------------------------------------------------------------
    # SD — 4 articles
    # -----------------------------------------------------------------------
    {
        "title": "V1 801 Error: Billing Document Creation Failures in VF01",
        "content": (
            "Error V1 801 ('Billing is blocked due to billing block') is one of the most common SD "
            "billing errors. It prevents VF01 from creating billing documents against deliveries or "
            "sales orders that have been placed on hold.\n\n"
            "Finding the block reason: (1) In VA03 (display sales order) or VL03N (display delivery), "
            "check the header tab for a billing block indicator. (2) The block reason is shown as a "
            "key — check customizing (OVVN) for block reason description.\n\n"
            "Common billing blocks and their causes: "
            "Credit block: Customer has exceeded credit limit (FD32). Contact credit controller to review "
            "and release via VKM3 or FD32. "
            "Complaint block: Sales order was flagged as a dispute. Resolve the complaint and remove block. "
            "Output not processed: Required output (proforma, packing slip) not yet processed — complete "
            "output in VL02N before billing. "
            "Incomplete data: Missing required fields — use VA02/VL02N to complete.\n\n"
            "Resolution: (1) Identify and resolve the root cause (do not just remove the block without "
            "understanding why it was set). (2) Remove billing block via VA02 (order level) or VL02N "
            "(delivery level). (3) Re-run VF01 or VF04 (mass billing).\n\n"
            "For India GST: Ensure GSTIN of billing party is maintained before billing — missing GSTIN "
            "causes V1 801 with a GST-specific message in India-localized systems."
        ),
        "module": "SD",
        "error_codes": ["V1 801"],
        "tcodes": ["VF01", "VF04", "VA02", "VA03", "VL02N", "VKM3", "FD32"],
        "tags": ["billing", "V1-801", "billing-block", "VF01", "SD"],
    },
    {
        "title": "VN 008 Error: Output (Message) Determination and EDI Issues",
        "content": (
            "VN 008 indicates a failure in SAP output determination — the system cannot find a valid "
            "condition record for an output type (invoice, order confirmation, delivery note, etc.). "
            "This blocks document output and EDI message transmission.\n\n"
            "Diagnosis: (1) In the document (VA03/VF03/VL03N), go to Extras → Output → Header. "
            "(2) Check the status of each output type — a red light indicates failure. "
            "(3) Select the failing output type → Processing Log to see the exact error message.\n\n"
            "Common causes: (1) Missing condition record in VV11/VV31 for the output type. The condition "
            "record maps the document characteristics to a printer/EDI partner. "
            "(2) Partner profile not maintained in WE20 for EDI transmission. "
            "(3) Communication method (printer, EDI, email) not properly configured. "
            "(4) Output program (NAST) running into an error — check with ST22.\n\n"
            "Resolution for EDI: (1) Verify partner profile in WE20 — confirm message type INVOIC/ORDERS "
            "is set up for the partner. (2) Check SCOT for email/fax configuration. "
            "(3) For IDoc processing, use WE09 to find and reprocess failed IDocs.\n\n"
            "Reprocessing stuck outputs: Use VF31/V22D to reprocess billing outputs in bulk. "
            "For delivery outputs: use MN05 (delivery output) or VL71 for delivery in transit."
        ),
        "module": "SD",
        "error_codes": ["VN 008"],
        "tcodes": ["VA03", "VF03", "VL03N", "VV11", "VV31", "WE20", "WE09", "VF31", "SCOT"],
        "tags": ["output", "EDI", "VN-008", "message-determination", "SD"],
    },
    {
        "title": "Customer Credit Management: Credit Blocks and FD32 Configuration",
        "content": (
            "Credit management in SAP SD prevents financial exposure by blocking orders and deliveries "
            "for customers who exceed their credit limit. Misconfiguration can cause legitimate orders "
            "to be blocked unnecessarily.\n\n"
            "Credit master analysis: (1) FD32 — View customer credit exposure, credit limit, and "
            "open items. Check: credit limit, credit horizon, and open items (orders + deliveries + "
            "open invoices). (2) FD33 for display-only view. (3) Credit exposure = open orders + "
            "open deliveries + open billing + AR open items.\n\n"
            "Common 'blocked despite valid limit' causes: (1) Credit check horizon: orders beyond "
            "the horizon date count toward credit exposure even if not due. Adjust in OVA8. "
            "(2) Individual credit limit by sales area not set — only overall limit defined. Check "
            "FD32 → Credit limit tab → Sales area-specific limits. "
            "(3) Credit group configuration in OVA8 — check which order types use which credit check.\n\n"
            "Releasing blocked orders: (1) VKM1 (blocked orders) → select → Release (VKM3/VKM4). "
            "(2) For temporary credit limit increase: update FD32 with approval documentation. "
            "(3) For batch release: VKM4 allows mass release with appropriate authorization.\n\n"
            "Notification setup: Configure automatic notification emails to credit controllers when "
            "customers approach 80% of limit via workflow from FD32 / FSCM credit management."
        ),
        "module": "SD",
        "error_codes": [],
        "tcodes": ["FD32", "FD33", "VKM1", "VKM3", "VKM4", "OVA8", "VA03"],
        "tags": ["credit-management", "credit-block", "FD32", "SD", "customer"],
    },
    {
        "title": "Pricing Condition Errors in SD Sales Orders",
        "content": (
            "Pricing in SAP SD is controlled by condition technique — access sequences determine which "
            "condition records are found and applied. Wrong prices in VA01 are usually a condition record "
            "or configuration issue.\n\n"
            "Analyzing pricing in a sales order: (1) In VA01/VA02, go to line item → Conditions tab. "
            "(2) Click 'Analysis' to see which condition records were found or missed. "
            "(3) Red conditions = not found (no record), yellow = found but overridden, green = active.\n\n"
            "Common causes of wrong prices: (1) Condition record for the correct price (customer+material "
            "combination) doesn't exist or expired. Create/extend via VK11. "
            "(2) Incorrect condition record scales — check if quantity breaks are incorrectly configured. "
            "(3) Price list assignment wrong on customer master (XD02 → Sales tab → Price List). "
            "(4) Manual price override in old order — if copy-controlled, manual price carries forward.\n\n"
            "For Indian-specific pricing (Excise/GST): "
            "Verify condition types for IGST, CGST, SGST are correctly configured in tax procedure "
            "TAXINN. Check J1ID for plant/material excise defaults.\n\n"
            "Mass price update: For blanket price changes, use VK12 (change condition records) with "
            "mass update capability. Always test in QAS first before applying to production condition records."
        ),
        "module": "SD",
        "error_codes": [],
        "tcodes": ["VA01", "VA02", "VK11", "VK12", "XD02"],
        "tags": ["pricing", "condition-record", "SD", "sales-order", "VK11"],
    },

    # -----------------------------------------------------------------------
    # PI/PO — 3 articles
    # -----------------------------------------------------------------------
    {
        "title": "XIAdapter / PI System: Interface Monitoring and Error Recovery",
        "content": (
            "SAP PI/PO (Process Integration/Process Orchestration) handles system-to-system integration. "
            "Interface failures impact downstream processes like GST filing, vendor portals, and bank connectivity.\n\n"
            "Primary monitoring tool: SXMB_MONI (Integration Engine monitoring). "
            "Status icons: green=processed, yellow=in process, red=error. "
            "For adapter errors: go to RWB (Runtime Workbench) → Component Monitoring → Adapter Engine.\n\n"
            "Common XIAdapter errors: (1) Connection timeout to external system — check network and "
            "target system availability. (2) SSL/Certificate expired — check STRUST on PI server for "
            "certificate validity. (3) Authentication failure — verify receiver agreement credentials.\n\n"
            "IDoc reprocessing: (1) WE02/WE09 to find failed IDocs by message type and date. "
            "(2) Select failed IDocs → Edit → Reprocess. (3) For large volumes, use SARA for archiving "
            "old IDocs before reprocessing current failures.\n\n"
            "Error recovery procedure: (1) Fix the root cause (network, certificate, data quality). "
            "(2) In SXMB_MONI, select failed messages → right-click → Restart. "
            "(3) Monitor re-processed messages for 5 minutes to confirm success. "
            "(4) If repeated failure, escalate to middleware team with full RWB logs.\n\n"
            "For ClearTax India integration: Ensure GST API credentials are current and the outbound "
            "GSTIN service endpoint is accessible from the PI server."
        ),
        "module": "PI_PO",
        "error_codes": ["IDOC_ERROR", "XIAdapter"],
        "tcodes": ["SXMB_MONI", "WE02", "WE09", "RWB", "STRUST", "SXI_MONITOR"],
        "tags": ["PI-PO", "integration", "IDoc", "XIAdapter", "interface-monitoring"],
    },
    {
        "title": "IDoc Processing: IDOC_ERROR Troubleshooting Guide",
        "content": (
            "IDocs (Intermediate Documents) are SAP's standard format for electronic data interchange. "
            "IDOC_ERROR status indicates the IDoc was received but could not be processed by the "
            "application function module.\n\n"
            "IDoc status codes: Status 02=Error passing data to application, Status 51=Application "
            "document not posted, Status 53=Application document posted, Status 64=IDoc ready to be "
            "transferred. Focus on status 51 and 02 for errors.\n\n"
            "Diagnosis via WE02/WE05: (1) Find the IDoc by message type and date. "
            "(2) Double-click → select 'Status Records' to see the processing history. "
            "(3) Click the error status record → click 'Error Message' to see the application error. "
            "This is the actual SAP error that prevented posting.\n\n"
            "Common application errors and fixes: "
            "Posting period closed (FI IDocs): Open period in OB52 then reprocess. "
            "Material not found (MM IDocs): Create/extend material master MM01 then reprocess. "
            "Customer/vendor not found: Create master data first. "
            "Duplicate document number: IDoc was already processed — check if it's a genuine duplicate "
            "or a data quality issue.\n\n"
            "Mass reprocessing: BD87 (status monitor for IDocs) allows mass reprocessing with filters. "
            "For automatic reprocessing, configure in WE46 (activate error handling). "
            "After reprocessing, verify application document was created (BKPF/MKPF etc.)."
        ),
        "module": "PI_PO",
        "error_codes": ["IDOC_ERROR"],
        "tcodes": ["WE02", "WE05", "BD87", "WE46", "WE09"],
        "tags": ["IDoc", "IDOC_ERROR", "EDI", "PI-PO", "interface"],
    },
    {
        "title": "ClearTax GST Integration with SAP: Common Issues and Resolution",
        "content": (
            "ClearTax is a popular GST filing platform integrated with SAP for Indian companies. "
            "The integration typically uses a combination of SAP PI/PO and direct API calls to push "
            "GSTR data from SAP to ClearTax for filing.\n\n"
            "Common integration issues: (1) API token expiry — ClearTax API tokens have limited validity. "
            "Check the integration configuration for the API endpoint and refresh the token. "
            "(2) Data format mismatch — SAP GSTIN format vs ClearTax expected format. "
            "Verify using J1IGST or ZGSTIN custom programs. "
            "(3) Missing HSN/SAC codes — items without HSN codes will fail ClearTax validation. "
            "Update material masters with HSN codes in J1ID.\n\n"
            "Reconciliation process: (1) Extract SAP data using RFUMSV00 (advance return for tax). "
            "(2) Compare with ClearTax portal data — focus on mismatches in invoice amounts and GSTIN. "
            "(3) For vendor GSTR-2A mismatches: vendor may have filed differently — raise dispute and "
            "hold payment until resolved.\n\n"
            "Emergency procedure (filing deadline): If integration is down near filing deadline: "
            "(1) Export data from SAP as Excel using standard reports. "
            "(2) Upload manually to ClearTax portal. "
            "(3) File returns manually for the period. "
            "(4) Fix integration and reconcile in next period.\n\n"
            "Support contacts: Raise ticket with ClearTax support if API errors continue beyond 2 hours. "
            "Provide error logs from SXMB_MONI or the custom middleware component."
        ),
        "module": "PI_PO",
        "error_codes": [],
        "tcodes": ["SXMB_MONI", "J1IGST", "RFUMSV00"],
        "tags": ["ClearTax", "GST", "India", "integration", "API", "GSTR"],
    },

    # -----------------------------------------------------------------------
    # ABAP — 2 articles
    # -----------------------------------------------------------------------
    {
        "title": "Transport Errors: SYNTAX_ERROR and Post-Transport ABAP Issues",
        "content": (
            "Transport-related ABAP errors occur when code changes move between systems with different "
            "states (kernel versions, note levels, other active objects). SYNTAX_ERROR after transport "
            "is particularly disruptive as it prevents a program from running entirely.\n\n"
            "Immediate diagnosis: (1) In SE38, open the program and click 'Check' to see syntax errors. "
            "(2) Check if the error references a method, class, or type that doesn't exist in the target "
            "system — these are often objects that weren't included in the transport. "
            "(3) Use STMS import log to confirm what else was imported at the same time.\n\n"
            "Missing dependent objects: (1) Use SE80 → Where-used list to identify dependencies. "
            "(2) Check if any referenced objects (classes, function modules, data elements) exist in "
            "the target system — they may need to be transported separately. "
            "(3) Transaction SCWB (Software Component Workbench) to analyze transport dependencies.\n\n"
            "Rollback procedure: If the syntax error is causing production impact: "
            "(1) In STMS, it's not possible to automatically 'undo' a transport. "
            "(2) Create a new correction transport that restores the previous object version. "
            "(3) In SE09, find the previous version in the object history (right-click → Object History). "
            "(4) Or restore from the backup of the transport request (from /usr/sap/trans/data/).\n\n"
            "Prevention: Always use transport checks in STMS before importing to production. "
            "Consider using CTS+ (enhanced change and transport system) for better dependency tracking."
        ),
        "module": "ABAP",
        "error_codes": ["SYNTAX_ERROR"],
        "tcodes": ["SE38", "SE80", "STMS", "SE09", "SCWB"],
        "tags": ["transport", "ABAP", "SYNTAX_ERROR", "SE38", "debug"],
    },
    {
        "title": "ABAP Dump Analysis and Performance Optimization with ST22",
        "content": (
            "ST22 (ABAP Runtime Error Analysis) is the starting point for all ABAP dump investigations. "
            "Understanding dump analysis leads to faster resolution and prevents recurrence.\n\n"
            "Reading a dump: (1) Exception class: The error type (e.g., CX_SY_ZERO_DIVIDE, "
            "CX_SY_DYNAMIC_OSQL_SEMANTICS). Different classes indicate different root causes. "
            "(2) Source code extract: Shows the exact line that caused the error — critical for dev team. "
            "(3) Active calls: The call stack showing which function/form called what. "
            "(4) System variables: SY-SUBRC, SY-TABIX at time of crash.\n\n"
            "Common dump classes and root causes: "
            "CX_SY_ZERO_DIVIDE: Division by zero — add DIVIDE-BY-ZERO check in code. "
            "CX_SY_CONVERSION_NO_NUMBER: String-to-number conversion failed — data quality issue. "
            "CX_SY_OPEN_SQL_DB: Database error — check if table structure changed without transport. "
            "DYNPRO_FIELD_CONVERSION: Screen field type mismatch after enhancement.\n\n"
            "Performance debugging with ST12: (1) Activate trace in ST12 for user + transaction. "
            "(2) Execute the slow transaction. (3) Analyze trace: sort by gross time to find "
            "expensive database selects. (4) Add secondary indexes (SE11) for repeatedly slow table scans "
            "on large tables.\n\n"
            "SAP Notes: Always search SAP support portal (support.sap.com) with the exception class "
            "and program name. SAP frequently publishes correction notes for known dump scenarios."
        ),
        "module": "ABAP",
        "error_codes": ["ABAP_RUNTIME_ERROR", "SYNTAX_ERROR"],
        "tcodes": ["ST22", "ST12", "SE11", "SE38", "SE80"],
        "tags": ["ABAP", "dump", "ST22", "performance", "debugging"],
    },
]

assert len(KB_ARTICLES) == 30, f"Expected 30 articles, got {len(KB_ARTICLES)}"

OUTPUT_DIR.joinpath("kb_articles.json").write_text(
    json.dumps(KB_ARTICLES, indent=2, ensure_ascii=False)
)

from collections import Counter
mod_counts = Counter(a["module"] for a in KB_ARTICLES)
print(f"Generated {len(KB_ARTICLES)} KB articles:")
print(f"  Module distribution: {dict(mod_counts)}")
print(f"\nSaved to: {OUTPUT_DIR}/kb_articles.json")
