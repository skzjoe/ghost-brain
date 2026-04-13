class GhostCoreError(Exception):
    """Base error for Ghost core."""


class BackendUnavailable(GhostCoreError):
    """Raised when an optional Ghost backend cannot be reached."""


class UnsafeContentRejected(GhostCoreError):
    """Raised when content is blocked by safety scanning."""


class InvalidWorkspace(GhostCoreError):
    """Raised when workspace paths are invalid or missing."""
