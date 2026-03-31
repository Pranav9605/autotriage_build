"""Dashboard service — KPI and accuracy aggregation queries."""

import logging
from sqlalchemy import Float, cast, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import Feedback
from app.models.ticket import Ticket
from app.models.triage_decision import TriageDecision
from app.schemas.dashboard import ConfidenceBucket, DashboardKPIs, ModuleAccuracy

logger = logging.getLogger(__name__)


class DashboardService:
    async def get_kpis(self, db: AsyncSession, tenant_id: str) -> DashboardKPIs:
        # Ticket counts
        ticket_counts = await db.execute(
            select(
                func.count(Ticket.id).label("total"),
                func.count(case((Ticket.status == "triaged", 1))).label("triaged"),
            ).where(Ticket.tenant_id == tenant_id)
        )
        tc = ticket_counts.one()

        # Triage aggregates
        triage_agg = await db.execute(
            select(
                func.avg(TriageDecision.confidence).label("avg_confidence"),
                func.avg(cast(TriageDecision.latency_ms, Float)).label("avg_latency"),
                func.count(case((TriageDecision.manual_review_required.is_(True), 1))).label("manual_review"),
            ).where(TriageDecision.tenant_id == tenant_id)
        )
        ta = triage_agg.one()

        # Feedback aggregates
        feedback_agg = await db.execute(
            select(
                func.count(Feedback.id).label("total_feedback"),
                func.count(case((Feedback.action == "accepted", 1))).label("accepted"),
                func.count(case((Feedback.action == "overridden", 1))).label("overridden"),
            ).where(Feedback.tenant_id == tenant_id)
        )
        fa = feedback_agg.one()

        total_feedback = fa.total_feedback or 0
        accepted = fa.accepted or 0
        overridden = fa.overridden or 0

        accuracy_rate = accepted / total_feedback if total_feedback > 0 else 0.0
        override_rate = overridden / total_feedback if total_feedback > 0 else 0.0

        # MTTR — avg hours from ticket created_at to resolved_at
        mttr_result = await db.execute(
            select(
                func.avg(
                    func.extract("epoch", Ticket.resolved_at - Ticket.created_at) / 3600
                ).label("mttr_hours")
            ).where(
                Ticket.tenant_id == tenant_id,
                Ticket.resolved_at.isnot(None),
            )
        )
        mttr_row = mttr_result.scalar_one_or_none()

        return DashboardKPIs(
            total_tickets=tc.total or 0,
            triaged_tickets=tc.triaged or 0,
            accuracy_rate=round(accuracy_rate, 4),
            override_rate=round(override_rate, 4),
            avg_confidence=round(float(ta.avg_confidence or 0.0), 4),
            avg_latency_ms=round(float(ta.avg_latency or 0.0), 1),
            manual_review_count=ta.manual_review or 0,
            mttr_hours=round(float(mttr_row), 2) if mttr_row else None,
        )

    async def get_module_accuracy(
        self, db: AsyncSession, tenant_id: str
    ) -> list[ModuleAccuracy]:
        rows = await db.execute(
            select(
                Feedback.final_module.label("module"),
                func.count(Feedback.id).label("total"),
                func.count(case((Feedback.is_correct_module.is_(True), 1))).label("correct"),
                func.count(case((Feedback.action == "overridden", 1))).label("override_count"),
                # Most common override category via a simple mode approximation
                func.mode().within_group(Feedback.override_category).label("most_common_override"),
            )
            .where(Feedback.tenant_id == tenant_id)
            .group_by(Feedback.final_module)
            .order_by(func.count(Feedback.id).desc())
        )

        results = []
        for row in rows:
            total = row.total or 1
            results.append(
                ModuleAccuracy(
                    module=row.module,
                    total=row.total,
                    correct=row.correct,
                    accuracy=round(row.correct / total, 4),
                    override_count=row.override_count,
                    most_common_override_category=row.most_common_override,
                )
            )
        return results

    async def get_confidence_distribution(
        self, db: AsyncSession, tenant_id: str
    ) -> list[ConfidenceBucket]:
        # Pull all (confidence, is_correct_module) pairs
        rows = await db.execute(
            select(
                TriageDecision.confidence,
                Feedback.is_correct_module,
            )
            .join(Feedback, Feedback.triage_decision_id == TriageDecision.id, isouter=True)
            .where(TriageDecision.tenant_id == tenant_id)
        )

        # Build buckets manually (0.0-0.1 … 0.9-1.0)
        buckets: dict[str, dict] = {}
        for lower in [i / 10 for i in range(10)]:
            upper = round(lower + 0.1, 1)
            label = f"{lower:.1f}-{upper:.1f}"
            buckets[label] = {"count": 0, "correct": 0}

        for row in rows:
            conf = float(row.confidence or 0.0)
            idx = min(int(conf * 10), 9)
            lower = idx / 10
            upper = round(lower + 0.1, 1)
            label = f"{lower:.1f}-{upper:.1f}"
            buckets[label]["count"] += 1
            if row.is_correct_module is True:
                buckets[label]["correct"] += 1

        results = []
        for label, data in buckets.items():
            count = data["count"]
            correct = data["correct"]
            results.append(
                ConfidenceBucket(
                    bucket=label,
                    count=count,
                    actual_accuracy=round(correct / count, 4) if count > 0 else 0.0,
                )
            )
        return results
