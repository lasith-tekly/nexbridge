"""
NexBridge Pluggable LLM Abstraction

Provides a single entry point for all LLM interactions.
Supports multiple providers (Anthropic, Ollama, OpenAI, etc.)
based on environment configuration.

All agents must import from here — never import provider
classes (e.g., ChatAnthropic) directly.
"""

import os
from langchain_core.language_models import BaseChatModel


def get_llm(provider: str = None) -> BaseChatModel:
    """
    Returns a configured LLM instance based on provider.

    Args:
        provider: Optional provider override. If None, reads from
                  LLM_PROVIDER environment variable (default: "anthropic")

    Returns:
        Configured BaseChatModel instance

    Raises:
        ValueError: If provider is not supported
        ImportError: If required provider package is not installed

    Supported providers:
        - "anthropic": Claude models via Anthropic API (default)
        - "ollama": Self-hosted models via Ollama
        - "openai": OpenAI API models

    Example:
        >>> from backend.core.llm import get_llm
        >>> llm = get_llm()  # Uses LLM_PROVIDER from env
        >>> llm = get_llm(provider="ollama")  # Override for testing
    """

    # Determine provider
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "anthropic").lower()

    provider = provider.lower()

    # Lazy import based on provider
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.0,  # Deterministic for safety-critical applications
        )

    elif provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama2"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.0,
        )

    elif provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.0,
        )

    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported: anthropic, ollama, openai"
        )
