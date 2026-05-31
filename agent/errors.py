"""Shared exception types for vision backends."""


class VisionClientError(Exception):
    """Vision backend request or response failure."""


class VisionParseError(VisionClientError):
    """Raised when a vision model returns unparseable or invalid action JSON."""
