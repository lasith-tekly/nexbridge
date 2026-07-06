"""
NexBridge Custom Exception Hierarchy

Defines all custom exceptions for the NexBridge transformation pipeline.
Every agent raises specific exceptions with full context for debugging
and error handling. Generic Python exceptions are not acceptable.

Part of the NexBridge transformation pipeline.
See docs/SOLUTION_AGENTS.md for full specification.
"""

from typing import Optional


class NexBridgeError(Exception):
    """
    Base exception for all NexBridge errors.
    All custom exceptions inherit from this class.

    Raised when: Any error occurs in the NexBridge pipeline.
    """

    def __init__(self, message: str, context: Optional[dict] = None):
        """
        Initialize NexBridge base exception.

        Args:
            message: Human-readable error message
            context: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        """Return formatted error message with context if present."""
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} | Context: {context_str}"
        return self.message


# --- Classification Exceptions ---

class ClassificationError(NexBridgeError):
    """
    Raised when a field cannot be classified by the registry.

    This typically occurs when:
    - Field name not found in registry.json
    - Registry file is malformed or missing
    - Field classification logic fails unexpectedly
    """

    def __init__(
        self,
        field_name: str,
        message: Optional[str] = None,
        context: Optional[dict] = None
    ):
        """
        Initialize classification error.

        Args:
            field_name: The field that could not be classified
            message: Optional custom error message
            context: Optional additional context
        """
        self.field_name = field_name

        if message is None:
            message = f"Field '{field_name}' could not be classified"

        super().__init__(message, context)

    def __str__(self) -> str:
        """Return formatted error with field name."""
        base = f"[CLASSIFICATION ERROR] {self.message}"
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{base} | Context: {context_str}"
        return base


# --- Threshold Exceptions ---

class T1ThresholdError(NexBridgeError):
    """
    Raised when a T1 (Safety Critical) field confidence is below 1.0.

    T1 fields require 100% confidence before the orchestrator
    can release the payload. Any value below 1.0 triggers HOLD.
    """

    def __init__(
        self,
        field_name: str,
        confidence: float,
        required: float = 1.0,
        message: Optional[str] = None,
        context: Optional[dict] = None
    ):
        """
        Initialize T1 threshold error.

        Args:
            field_name: The T1 field that failed threshold check
            confidence: The actual confidence score received
            required: The required threshold (always 1.0 for T1)
            message: Optional custom error message
            context: Optional additional context
        """
        self.field_name = field_name
        self.confidence = confidence
        self.required = required

        if message is None:
            message = (
                f"T1 field '{field_name}' confidence {confidence:.2f} "
                f"below required threshold {required}"
            )

        super().__init__(message, context)

    def __str__(self) -> str:
        """Return formatted error with all threshold details."""
        return (
            f"[T1 THRESHOLD ERROR] field={self.field_name} "
            f"confidence={self.confidence:.2f} required={self.required}"
        )


class T2ThresholdError(NexBridgeError):
    """
    Raised when a T2 (Operationally Sensitive) field confidence is below 0.95.

    T2 fields require 95% confidence before the orchestrator
    can release the payload. Any value below 0.95 triggers HOLD.
    """

    def __init__(
        self,
        field_name: str,
        confidence: float,
        required: float = 0.95,
        message: Optional[str] = None,
        context: Optional[dict] = None
    ):
        """
        Initialize T2 threshold error.

        Args:
            field_name: The T2 field that failed threshold check
            confidence: The actual confidence score received
            required: The required threshold (always 0.95 for T2)
            message: Optional custom error message
            context: Optional additional context
        """
        self.field_name = field_name
        self.confidence = confidence
        self.required = required

        if message is None:
            message = (
                f"T2 field '{field_name}' confidence {confidence:.2f} "
                f"below required threshold {required}"
            )

        super().__init__(message, context)

    def __str__(self) -> str:
        """Return formatted error with all threshold details."""
        return (
            f"[T2 THRESHOLD ERROR] field={self.field_name} "
            f"confidence={self.confidence:.2f} required={self.required}"
        )


# --- Divergence Exceptions ---

class DivergenceError(NexBridgeError):
    """
    Raised when dual-agent verification detects divergence on a T1 field.

    For T1 fields, the interpreter runs twice independently (Run1 and Run2).
    If the two runs map the field to different target fields, this is a
    divergence and triggers an immediate HOLD decision.
    """

    def __init__(
        self,
        field_name: str,
        run1_target: str,
        run2_target: str,
        run1_confidence: float,
        run2_confidence: float,
        message: Optional[str] = None,
        context: Optional[dict] = None
    ):
        """
        Initialize divergence error.

        Args:
            field_name: The T1 field that diverged
            run1_target: Target field from Run1
            run2_target: Target field from Run2
            run1_confidence: Confidence from Run1
            run2_confidence: Confidence from Run2
            message: Optional custom error message
            context: Optional additional context
        """
        self.field_name = field_name
        self.run1_target = run1_target
        self.run2_target = run2_target
        self.run1_confidence = run1_confidence
        self.run2_confidence = run2_confidence

        if message is None:
            message = (
                f"T1 field '{field_name}' diverged: "
                f"Run1={run1_target} (conf={run1_confidence:.2f}), "
                f"Run2={run2_target} (conf={run2_confidence:.2f})"
            )

        super().__init__(message, context)

    def __str__(self) -> str:
        """Return formatted error with full divergence details."""
        return (
            f"[DIVERGENCE ERROR] field={self.field_name} "
            f"run1_target={self.run1_target} run1_conf={self.run1_confidence:.2f} "
            f"run2_target={self.run2_target} run2_conf={self.run2_confidence:.2f}"
        )


# --- Pipeline Exceptions ---

class TranslationError(NexBridgeError):
    """
    Raised when the translator cannot build the JSON output.

    This occurs when:
    - Field mapping cannot be converted to target schema format
    - Target schema validation fails
    - Required field is missing from mappings
    """

    def __init__(
        self,
        field_name: str,
        reason: str,
        message: Optional[str] = None,
        context: Optional[dict] = None
    ):
        """
        Initialize translation error.

        Args:
            field_name: The field that failed translation
            reason: Why the translation failed
            message: Optional custom error message
            context: Optional additional context
        """
        self.field_name = field_name
        self.reason = reason

        if message is None:
            message = f"Translation failed for field '{field_name}': {reason}"

        super().__init__(message, context)

    def __str__(self) -> str:
        """Return formatted error with field and reason."""
        return f"[TRANSLATION ERROR] field={self.field_name} reason={self.reason}"


class OrchestratorError(NexBridgeError):
    """
    Raised when orchestrator decision logic fails.

    This is a critical error indicating the orchestrator
    could not make a GO/HOLD/ESCALATE decision. This should
    rarely occur and indicates a bug in orchestration logic.
    """

    def __init__(
        self,
        reason: str,
        message: Optional[str] = None,
        context: Optional[dict] = None
    ):
        """
        Initialize orchestrator error.

        Args:
            reason: Why the orchestrator failed
            message: Optional custom error message
            context: Optional additional context
        """
        self.reason = reason

        if message is None:
            message = f"Orchestrator decision logic failed: {reason}"

        super().__init__(message, context)

    def __str__(self) -> str:
        """Return formatted error with reason."""
        return f"[ORCHESTRATOR ERROR] {self.reason}"


class AuditError(NexBridgeError):
    """
    Raised when an audit entry cannot be written.

    This is a critical error as audit entries are immutable
    and required for compliance. If audit logging fails,
    the entire pipeline must halt.
    """

    def __init__(
        self,
        reason: str,
        message: Optional[str] = None,
        context: Optional[dict] = None
    ):
        """
        Initialize audit error.

        Args:
            reason: Why the audit entry could not be written
            message: Optional custom error message
            context: Optional additional context
        """
        self.reason = reason

        if message is None:
            message = f"Audit entry could not be written: {reason}"

        super().__init__(message, context)

    def __str__(self) -> str:
        """Return formatted error with reason."""
        return f"[AUDIT ERROR] {self.reason}"


class LLMError(NexBridgeError):
    """
    Raised when an LLM call fails or returns invalid output.

    This occurs when:
    - API timeout or rate limit
    - Invalid API key or authentication failure
    - LLM returns malformed output
    - Provider service is unavailable
    """

    def __init__(
        self,
        provider: str,
        reason: str,
        message: Optional[str] = None,
        context: Optional[dict] = None
    ):
        """
        Initialize LLM error.

        Args:
            provider: The LLM provider that failed (anthropic, ollama, openai)
            reason: Why the LLM call failed
            message: Optional custom error message
            context: Optional additional context
        """
        self.provider = provider
        self.reason = reason

        if message is None:
            message = f"LLM call failed for provider '{provider}': {reason}"

        super().__init__(message, context)

    def __str__(self) -> str:
        """Return formatted error with provider and reason."""
        return f"[LLM ERROR] provider={self.provider} reason={self.reason}"


# --- Registry Exceptions ---

class RegistryNotFoundError(NexBridgeError):
    """
    Raised when a requested registry_id cannot be found in REGISTRY_DIR.

    This occurs when:
    - REGISTRY_DIR is set but {registry_id}.json does not exist in it
    - The requested registry_id is misspelled or not yet created
    """

    def __init__(
        self,
        registry_id: str,
        available: list[str],
        message: Optional[str] = None,
        context: Optional[dict] = None
    ):
        """
        Initialize registry not found error.

        Args:
            registry_id: The registry ID that was requested
            available: List of registry IDs that do exist
            message: Optional custom error message
            context: Optional additional context
        """
        self.registry_id = registry_id
        self.available = available

        if message is None:
            available_str = ", ".join(available) if available else "(none)"
            message = (
                f"Registry '{registry_id}' not found. "
                f"Available: {available_str}"
            )

        super().__init__(message, context)

    def __str__(self) -> str:
        """Return formatted error with registry_id and available list."""
        available_str = ", ".join(self.available) if self.available else "(none)"
        return (
            f"[REGISTRY NOT FOUND] registry_id={self.registry_id} "
            f"available={available_str}"
        )


# --- Parser Exceptions ---

class ParseError(NexBridgeError):
    """
    Raised when input payload cannot be parsed.

    This occurs when:
    - XML is malformed or not well-formed
    - Input format does not match expected structure
    """

    def __init__(
        self,
        input_format: str,
        reason: str,
        message: Optional[str] = None,
        context: Optional[dict] = None
    ):
        """
        Initialize parse error.

        Args:
            input_format: The input format that failed (e.g. "xml")
            reason: Why parsing failed
            message: Optional custom error message
            context: Optional additional context
        """
        self.input_format = input_format
        self.reason = reason

        if message is None:
            message = f"Failed to parse {input_format} payload: {reason}"

        super().__init__(message, context)

    def __str__(self) -> str:
        """Return formatted error with format and reason."""
        return f"[PARSE ERROR] format={self.input_format} reason={self.reason}"
