"""Custom exception hierarchy for AutoTriage."""


class AutoTriageException(Exception):
    """Base exception for all AutoTriage errors."""

    def __init__(self, message: str = "", status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class TenantNotFoundError(AutoTriageException):
    def __init__(self, tenant_id: str) -> None:
        super().__init__(f"Tenant not found: {tenant_id}", status_code=404)
        self.tenant_id = tenant_id


class TicketNotFoundError(AutoTriageException):
    def __init__(self, ticket_id: str) -> None:
        super().__init__(f"Ticket not found: {ticket_id}", status_code=404)
        self.ticket_id = ticket_id


class TriageEngineError(AutoTriageException):
    def __init__(self, message: str = "Triage engine failed") -> None:
        super().__init__(message, status_code=502)


class RetrievalError(AutoTriageException):
    def __init__(self, message: str = "Retrieval failed") -> None:
        super().__init__(message, status_code=500)


class ConfigurationError(AutoTriageException):
    def __init__(self, message: str = "Configuration error") -> None:
        super().__init__(message, status_code=500)
