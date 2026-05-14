class AgentRuntimeError(Exception):
    """Base exception for agent runtime contract errors."""


class AgentFallbackError(AgentRuntimeError):
    """Raised when deterministic fallback cannot produce a result."""
