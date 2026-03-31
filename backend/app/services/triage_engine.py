"""Triage engine — abstract interface + Claude (Anthropic) implementation."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

from anthropic import AsyncAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.exceptions import TriageEngineError
from app.schemas.triage import TriageDecisionSchema, TriageRequest

logger = logging.getLogger(__name__)


class TriageEngine(ABC):
    @abstractmethod
    async def classify(self, request: TriageRequest) -> tuple[TriageDecisionSchema, int]:
        """Classify a ticket.

        Returns:
            (decision, tokens_used) — tokens_used is 0 if unavailable.
        """
        ...


class ClaudeTriageEngine(TriageEngine):
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
    ) -> None:
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    def _build_system_prompt(self, request: TriageRequest) -> str:
        cfg = request.tenant_config
        modules = ", ".join(cfg.get("modules_active", []))
        teams = cfg.get("teams", {})
        teams_str = "\n".join(f"  {mod}: {team}" for mod, team in teams.items())

        similar_section = ""
        if request.similar_tickets:
            lines = ["Similar resolved tickets (use as reference context):"]
            for t in request.similar_tickets:
                lines.append(
                    f"  - [{t.result_id}] score={t.final_score:.2f}: {t.content[:200]}"
                )
            similar_section = "\n".join(lines) + "\n\n"

        kb_section = ""
        if request.kb_articles:
            lines = ["Relevant KB articles:"]
            for kb in request.kb_articles:
                lines.append(f"  - [{kb.title}]: {kb.content[:300]}")
            kb_section = "\n".join(lines) + "\n\n"

        schema_example = json.dumps(
            {
                "module": "FI",
                "priority": "P2",
                "issue_type": "Technical Issue",
                "root_cause_hypothesis": "Brief hypothesis about root cause",
                "recommended_solution": "Step-by-step resolution recommendation",
                "assign_to": "SAP Finance Team",
                "confidence": 0.87,
                "manual_review_required": False,
                "similar_ticket_ids": [],
            },
            indent=2,
        )

        return f"""You are an SAP incident triage specialist. Classify the following SAP support ticket.

Available SAP modules for this tenant: {modules}

Team assignments:
{teams_str}

Priority criteria:
- P1: Production down, business-critical process completely blocked, data corruption risk
- P2: Major functionality impaired, workaround exists but is painful or temporary
- P3: Minor issue, workaround exists, non-urgent but should be fixed
- P4: Cosmetic issue, enhancement request, documentation update

{similar_section}{kb_section}Respond with ONLY valid JSON matching this schema exactly (no markdown, no explanation):
{schema_example}"""

    def _build_user_prompt(self, request: TriageRequest) -> str:
        return f"""Ticket ID: {request.ticket_id}
Source channel: {request.source}
Description: {request.description}
Transaction code (tcode): {request.tcode or 'Not specified'}
Error code: {request.error_code or 'Not specified'}
Environment: {request.environment or 'Not specified'}"""

    # ------------------------------------------------------------------
    # Classify
    # ------------------------------------------------------------------

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _call_claude(
        self, system: str, user: str, correction_hint: Optional[str] = None
    ) -> tuple[str, int]:
        """Call Claude and return (raw_text, tokens_used)."""
        messages = [{"role": "user", "content": user}]
        if correction_hint:
            messages.append({"role": "assistant", "content": correction_hint})
            messages.append(
                {
                    "role": "user",
                    "content": "Please output ONLY valid JSON with no markdown or extra text.",
                }
            )

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=0.1,
            system=system,
            messages=messages,
        )
        text = response.content[0].text if response.content else ""
        tokens = response.usage.input_tokens + response.usage.output_tokens
        return text, tokens

    async def classify(self, request: TriageRequest) -> tuple[TriageDecisionSchema, int]:
        system = self._build_system_prompt(request)
        user = self._build_user_prompt(request)

        try:
            raw_text, tokens = await self._call_claude(system, user)
        except Exception as exc:
            logger.error("Claude API call failed: %s", exc)
            raise TriageEngineError(f"LLM API call failed: {exc}") from exc

        # First parse attempt
        decision = _parse_decision(raw_text)
        if decision is not None:
            return decision, tokens

        logger.warning(
            "First parse failed for ticket=%s, retrying with correction hint",
            request.ticket_id,
        )

        # Retry with a correction prompt
        try:
            raw_text2, tokens2 = await self._call_claude(
                system, user, correction_hint=raw_text
            )
            tokens += tokens2
        except Exception as exc:
            logger.error("Claude correction retry failed: %s", exc)
            raise TriageEngineError(f"LLM correction retry failed: {exc}") from exc

        decision = _parse_decision(raw_text2)
        if decision is not None:
            return decision, tokens

        raise TriageEngineError(
            f"Could not parse LLM response as TriageDecisionSchema after 2 attempts. "
            f"Last response: {raw_text2[:200]}"
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_decision(text: str) -> Optional[TriageDecisionSchema]:
    """Try to parse raw LLM text into a TriageDecisionSchema. Returns None on failure."""
    text = text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(
            line for line in lines if not line.startswith("```")
        ).strip()

    try:
        data = json.loads(text)
        return TriageDecisionSchema.model_validate(data)
    except Exception as exc:
        logger.debug("JSON parse/validation failed: %s | text=%s", exc, text[:300])
        return None
