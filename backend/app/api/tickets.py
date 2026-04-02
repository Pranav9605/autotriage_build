"""Tickets API — create + list + get + SSE stream."""

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.dependencies import get_db, get_intake_service, get_tenant_id
from app.models.ticket import Ticket
from app.models.triage_decision import TriageDecision
from app.schemas.ticket import TicketCreate, TicketListResponse, TicketResponse
from app.schemas.triage import TriageResponse
from app.services.intake import IntakeService
from app import sse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/tickets", tags=["tickets"])


@router.get("/stream")
async def stream_tickets(
    request: Request,
    tenant_id: str = Depends(get_tenant_id),
):
    """Server-Sent Events stream — emits ticket_created, ticket_triaged, feedback_received."""

    async def event_generator():
        q = sse.register()
        try:
            # Initial ping so the client knows the connection is live
            yield {"event": "connected", "data": f'{{"tenant_id": "{tenant_id}"}}'}
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield {"event": "message", "data": payload}
                except asyncio.TimeoutError:
                    # Keepalive comment
                    yield {"event": "ping", "data": "{}"}
        finally:
            sse.unregister(q)

    return EventSourceResponse(event_generator())


@router.post("", response_model=TicketResponse, status_code=201)
async def create_ticket(
    body: TicketCreate,
    tenant_id: str = Depends(get_tenant_id),
    intake_service: IntakeService = Depends(get_intake_service),
    db: AsyncSession = Depends(get_db),
):
    """Create a ticket and run the full triage pipeline atomically."""
    triage = await intake_service.process_ticket(
        tenant_id=tenant_id,
        source=body.source,
        raw_text=body.raw_text,
        reporter=body.reporter,
    )

    result = await db.execute(
        select(Ticket).where(
            Ticket.id == triage.ticket_id,
            Ticket.tenant_id == tenant_id,
        )
    )
    ticket = result.scalar_one()
    response = _ticket_to_response(ticket, triage)

    await sse.broadcast("ticket_triaged", {
        "ticket_id": triage.ticket_id,
        "module": triage.module,
        "priority": triage.priority,
        "source": body.source,
        "tenant_id": tenant_id,
    })

    return response


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List tickets for the tenant with optional filters."""
    count_q = select(func.count(Ticket.id)).where(Ticket.tenant_id == tenant_id)
    if status:
        count_q = count_q.where(Ticket.status == status)

    total_result = await db.execute(count_q)
    total = total_result.scalar_one()

    q = (
        select(Ticket)
        .where(Ticket.tenant_id == tenant_id)
        .order_by(Ticket.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    if status:
        q = q.where(Ticket.status == status)

    rows = await db.execute(q)
    tickets = rows.scalars().all()

    ticket_ids = [t.id for t in tickets]
    triage_map: dict[str, TriageDecision] = {}
    if ticket_ids:
        td_result = await db.execute(
            select(TriageDecision)
            .where(
                TriageDecision.ticket_id.in_(ticket_ids),
                TriageDecision.tenant_id == tenant_id,
            )
            .order_by(TriageDecision.ticket_id, TriageDecision.version.desc())
        )
        for td in td_result.scalars():
            if td.ticket_id not in triage_map:
                triage_map[td.ticket_id] = td

    result_tickets = []
    for ticket in tickets:
        td = triage_map.get(ticket.id)
        if module and (td is None or td.module != module):
            continue
        if priority and (td is None or td.priority != priority):
            continue
        triage_resp = _triage_decision_to_response(td) if td else None
        result_tickets.append(_ticket_to_response(ticket, triage_resp))

    return TicketListResponse(
        tickets=result_tickets,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.tenant_id == tenant_id,
        )
    )
    ticket = result.scalar_one_or_none()
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    td_result = await db.execute(
        select(TriageDecision)
        .where(
            TriageDecision.ticket_id == ticket_id,
            TriageDecision.tenant_id == tenant_id,
        )
        .order_by(TriageDecision.version.desc())
        .limit(1)
    )
    td = td_result.scalar_one_or_none()
    triage_resp = _triage_decision_to_response(td) if td else None

    return _ticket_to_response(ticket, triage_resp)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _triage_decision_to_response(td: TriageDecision) -> TriageResponse:
    return TriageResponse(
        decision_id=td.id,
        ticket_id=td.ticket_id,
        module=td.module,
        priority=td.priority,
        issue_type=td.issue_type,
        root_cause_hypothesis=td.root_cause_hypothesis or "",
        recommended_solution=td.recommended_solution or "",
        assign_to=td.assign_to,
        confidence=td.confidence,
        confidence_calibrated=td.confidence_calibrated,
        classification_source=td.classification_source,
        model_version=td.model_version,
        rules_applied=td.rules_applied or [],
        similar_ticket_ids=td.similar_ticket_ids or [],
        similar_ticket_scores=td.similar_ticket_scores or [],
        kb_article_ids=td.kb_article_ids or [],
        manual_review_required=td.manual_review_required,
        review_reason=td.review_reason,
        latency_ms=td.latency_ms or 0,
    )


def _ticket_to_response(ticket: Ticket, triage: Optional[TriageResponse]) -> TicketResponse:
    return TicketResponse(
        id=ticket.id,
        tenant_id=ticket.tenant_id,
        source=ticket.source,
        description=ticket.description,
        tcode=ticket.tcode,
        error_code=ticket.error_code,
        environment=ticket.environment,
        reporter=ticket.reporter,
        status=ticket.status,
        created_at=ticket.created_at,
        triage=triage,
    )
