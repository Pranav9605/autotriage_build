import uuid
from datetime import datetime


def generate_ticket_id() -> str:
    """Generate a ticket ID in the format INC-{year}-{6-char hex}.

    Uses a random hex suffix for uniqueness without requiring DB coordination.
    Example: INC-2026-a3f2c1
    """
    year = datetime.now().year
    suffix = uuid.uuid4().hex[:6]
    return f"INC-{year}-{suffix}"


def generate_uuid() -> str:
    """Generate a random UUID4 string."""
    return str(uuid.uuid4())
