class OpsPilotError(Exception):
    """Base exception for OpsPilot."""


class LLMError(OpsPilotError):
    """Raised when the LLM cannot produce a valid diagnosis."""


class LLMTimeoutError(LLMError):
    """Raised when the LLM call exceeds the configured timeout."""


class LLMResponseError(LLMError):
    """Raised when the LLM returns an invalid response."""