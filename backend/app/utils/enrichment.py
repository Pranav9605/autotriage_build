"""SAP metadata extraction from unstructured ticket text."""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Known SAP transaction codes (used to anchor the regex)
# ---------------------------------------------------------------------------
_KNOWN_TCODES = {
    "FB50", "FB60", "F110", "MIRO", "ME21N", "MIGO", "MB1A",
    "VF01", "VA01", "VL01N", "VL02N", "VL03N",
    "SM21", "ST22", "SM50", "SE38", "SE80", "STMS",
    "SXMB_MONI", "SXI_MONITOR",
    "XD01", "XD02", "FK01", "FK02",
    "MM01", "MM02", "MB51", "MB52",
    "MASS", "LSMW", "SU01", "SU10", "PFCG", "STRUST",
    "F-02",
}

# General t-code pattern: 2-4 uppercase letters + 1-4 digits + optional uppercase letter.
# Requires 2+ letters to avoid matching single-letter error-code prefixes like "F5".
# Explicit prefix forms ("transaction FB50") still catch any case via group 1.
_TCODE_GENERAL = re.compile(
    r"(?:transaction|tcode|t-code|t_code)\s*[:\s]\s*([A-Z][A-Z0-9_-]{1,9})"
    r"|(?<![A-Z0-9_/-])([A-Z]{2,4}[-]?\d{1,4}[A-Z]?)(?![A-Z0-9_/-])",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# SAP error code patterns
# ---------------------------------------------------------------------------
# Format 1 & 2: "F5 301", "AA 500", "ME 573", "M8 108", "VN 008"
_ERROR_CODE_ALPHA_NUM = re.compile(
    r"\b([A-Z]{1,2}\d{0,1})\s+(\d{3})\b"
)
# Format 3: ABAP dump names
_ERROR_CODE_DUMP = re.compile(
    r"\b(ABAP_RUNTIME_ERROR|TIME_OUT|SYNTAX_ERROR|DUMP_ANALYSIS|"
    r"CALL_FUNCTION_REMOTE_ERROR|MESSAGE_TYPE_X|RAISE_EXCEPTION)\b"
)
# Format 4: Integration / IDoc
_ERROR_CODE_INTEGRATION = re.compile(
    r"\b(XIAdapter|IDOC_ERROR|XI_AF_MESSAGE_BROKER|IDOC_INBOUND_ASYNCHRONOUS)\b"
)

# ---------------------------------------------------------------------------
# Environment patterns
# ---------------------------------------------------------------------------
_ENV_MAP = {
    "PRD": "PRD", "PROD": "PRD", "PRODUCTION": "PRD",
    "QAS": "QAS", "QUALITY": "QAS", "QA": "QAS",
    "DEV": "DEV", "DEVELOPMENT": "DEV",
}

_ENV_PATTERN = re.compile(
    r"\b(PRD|PROD|PRODUCTION|QAS|QUALITY|QA|DEV|DEVELOPMENT)\b"
    r"|production\s+(?:system|server|env|environment|box)"
    r"|quality\s+(?:system|server|env|environment|box)"
    r"|dev(?:elopment)?\s+(?:system|server|env|environment|box)",
    re.IGNORECASE,
)


def extract_tcode(text: str) -> Optional[str]:
    """Extract the first SAP transaction code from text.

    Matches explicit prefixes ('transaction FB50', 'tcode: ME21N') first,
    then falls back to the general pattern anchored against the known list.
    """
    # Pass 1 — explicit prefix match (case-insensitive)
    for match in _TCODE_GENERAL.finditer(text):
        candidate = (match.group(1) or match.group(2) or "").upper().strip()
        if candidate:
            return candidate

    # Pass 2 — standalone known t-code anywhere in text (word boundary)
    for tcode in _KNOWN_TCODES:
        pattern = re.compile(r"(?<![A-Z0-9_/-])" + re.escape(tcode) + r"(?![A-Z0-9_/-])", re.IGNORECASE)
        if pattern.search(text):
            return tcode

    return None


def extract_error_code(text: str) -> Optional[str]:
    """Extract the first SAP error code from text."""
    # Dump names first (most specific)
    m = _ERROR_CODE_DUMP.search(text)
    if m:
        return m.group(1)

    # Integration errors
    m = _ERROR_CODE_INTEGRATION.search(text)
    if m:
        return m.group(1)

    # Alpha-numeric format e.g. "F5 301"
    m = _ERROR_CODE_ALPHA_NUM.search(text)
    if m:
        return f"{m.group(1)} {m.group(2)}"

    return None


def extract_environment(text: str) -> Optional[str]:
    """Extract and normalize SAP environment from text (PRD / QAS / DEV)."""
    m = _ENV_PATTERN.search(text)
    if not m:
        return None

    raw = m.group(0).upper().split()[0]  # get first word, uppercase
    # Normalize via map
    for key, value in _ENV_MAP.items():
        if raw.startswith(key):
            return value

    return None


def enrich_ticket(raw_text: str) -> dict:
    """Run all three extractors and return a dict with tcode, error_code, environment."""
    result = {
        "tcode": extract_tcode(raw_text),
        "error_code": extract_error_code(raw_text),
        "environment": extract_environment(raw_text),
    }
    logger.debug("Enrichment result: %s", result)
    return result
