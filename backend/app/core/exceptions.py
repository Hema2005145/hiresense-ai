"""
Custom exception hierarchy.

Every predictable failure mode in the app (not found, validation,
external API failure, parsing failure) should raise one of these
instead of a bare Exception or an HTTPException raised deep inside a
service. Services and repositories should never import FastAPI, so
they cannot raise HTTPException directly — they raise these, and the
global exception handler registered in main.py converts them into the
appropriate HTTP responses.

This keeps the service layer framework-agnostic: the same
ResumeParsingService could be reused in a CLI tool or a background
worker without dragging in FastAPI.
"""

from __future__ import annotations


class HireSenseError(Exception):
    """Base class for all application-specific exceptions."""

    #: Default HTTP status code used by the global exception handler
    #: when this exception (or a subclass that doesn't override it)
    #: propagates out of a route.
    status_code: int = 500
    #: Machine-readable error code returned in the API error envelope.
    error_code: str = "internal_error"

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(HireSenseError):
    """Raised when a requested entity does not exist."""

    status_code = 404
    error_code = "not_found"


class ValidationFailedError(HireSenseError):
    """
    Raised for domain-level validation failures that Pydantic's
    schema validation cannot catch (e.g. "resume has no extractable
    text", "job description is empty after parsing").
    """

    status_code = 422
    error_code = "validation_failed"


class ParsingError(HireSenseError):
    """Raised when a PDF or document cannot be parsed."""

    status_code = 422
    error_code = "parsing_error"


class UnsupportedFileTypeError(HireSenseError):
    """Raised when an uploaded file is not an accepted type."""

    status_code = 415
    error_code = "unsupported_file_type"


class FileTooLargeError(HireSenseError):
    """Raised when an uploaded file exceeds the configured size limit."""

    status_code = 413
    error_code = "file_too_large"


class ExternalServiceError(HireSenseError):
    """
    Raised when a downstream dependency (LLM provider, embedding
    service) fails or times out. Kept distinct from ParsingError so
    callers/monitoring can tell "our code is wrong" apart from
    "a third party is down".
    """

    status_code = 502
    error_code = "external_service_error"


class ModelNotTrainedError(HireSenseError):
    """Raised when an ML prediction is requested before any model has
    been trained and saved to the model registry."""

    status_code = 409
    error_code = "model_not_trained"
