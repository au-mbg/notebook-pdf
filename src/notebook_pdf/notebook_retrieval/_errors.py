"""Shared exceptions for notebook retrieval."""


class GetIpynbTimeoutError(TimeoutError):
    """Raised when notebook retrieval times out."""
    pass
