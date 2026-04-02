"""SSE event broadcaster — in-memory queues for real-time ticket updates."""

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Active SSE connections: set of asyncio.Queue, one per connected client
_connections: set[asyncio.Queue] = set()


def register() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=100)
    _connections.add(q)
    logger.debug("SSE client connected — total=%d", len(_connections))
    return q


def unregister(q: asyncio.Queue) -> None:
    _connections.discard(q)
    logger.debug("SSE client disconnected — total=%d", len(_connections))


async def broadcast(event_type: str, data: dict[str, Any]) -> None:
    """Push an event to all connected SSE clients (non-blocking)."""
    if not _connections:
        return
    payload = json.dumps({"event": event_type, **data})
    dead: list[asyncio.Queue] = []
    for q in list(_connections):
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        unregister(q)
