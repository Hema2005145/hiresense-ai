"""
LLM provider abstraction.

Every service that needs to call an LLM (RAG answering, interview
question generation, answer evaluation, resume rewriting) depends on
the `LLMProvider` interface below, never on a concrete SDK. This is
what makes "swap Gemini for OpenAI or Claude" a one-line config change
(`LLM_PROVIDER=openai` in .env) instead of a code change scattered
across every service that happens to call an LLM.

Design pattern: this is the Strategy pattern (interchangeable
algorithm/implementation behind a common interface) combined with a
simple Factory function that picks the concrete strategy based on
configuration.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.config import Settings, get_settings
from app.core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Normalized response shape returned by every provider.

    Keeping this provider-agnostic means calling code never has to
    know whether `text` came from Gemini's `.text`, OpenAI's
    `choices[0].message.content`, or Claude's `content[0].text` — each
    provider implementation does that translation once, here.
    """

    text: str
    model: str
    provider: str


class LLMProvider(ABC):
    """Abstract interface every concrete LLM provider must implement."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_output_tokens: int = 1024,
    ) -> LLMResponse:
        """
        Generates a single completion for `prompt`.

        Raises:
            ExternalServiceError: if the underlying API call fails.
        """
        raise NotImplementedError


class GeminiProvider(LLMProvider):
    """Google Gemini implementation of LLMProvider."""

    def __init__(self, api_key: str, model_name: str) -> None:
        if not api_key:
            raise ExternalServiceError(
                "Gemini API key is not configured. Set GEMINI_API_KEY in .env."
            )
        # Imported lazily so that installing/importing the google
        # SDK is only required when Gemini is the active provider —
        # keeps import time fast for anyone running with a different
        # provider configured.
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self._genai = genai
        self._model_name = model_name

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_output_tokens: int = 1024,
    ) -> LLMResponse:
        try:
            model = self._genai.GenerativeModel(
                model_name=self._model_name,
                system_instruction=system_prompt,
            )
            result = model.generate_content(
                prompt,
                generation_config=self._genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )
            return LLMResponse(
                text=result.text,
                model=self._model_name,
                provider="gemini",
            )
        except Exception as exc:  # noqa: BLE001 - normalize all SDK errors
            logger.exception("Gemini generation failed")
            raise ExternalServiceError(
                f"Gemini API call failed: {exc}"
            ) from exc


class OpenAIProvider(LLMProvider):
    """OpenAI implementation of LLMProvider.

    Included now, fully working, even though OpenAI is not the
    default — this is what proves the abstraction actually works
    rather than being a theoretical interface with one implementation.
    """

    def __init__(self, api_key: str, model_name: str) -> None:
        if not api_key:
            raise ExternalServiceError(
                "OpenAI API key is not configured. Set OPENAI_API_KEY in .env."
            )
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model_name = model_name

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_output_tokens: int = 1024,
    ) -> LLMResponse:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            completion = self._client.chat.completions.create(
                model=self._model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_output_tokens,
            )
            return LLMResponse(
                text=completion.choices[0].message.content or "",
                model=self._model_name,
                provider="openai",
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("OpenAI generation failed")
            raise ExternalServiceError(
                f"OpenAI API call failed: {exc}"
            ) from exc


class ClaudeProvider(LLMProvider):
    """Anthropic Claude implementation of LLMProvider."""

    def __init__(self, api_key: str, model_name: str) -> None:
        if not api_key:
            raise ExternalServiceError(
                "Anthropic API key is not configured. Set ANTHROPIC_API_KEY in .env."
            )
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model_name = model_name

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_output_tokens: int = 1024,
    ) -> LLMResponse:
        try:
            message = self._client.messages.create(
                model=self._model_name,
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_output_tokens,
            )
            text = "".join(
                block.text for block in message.content if block.type == "text"
            )
            return LLMResponse(
                text=text,
                model=self._model_name,
                provider="claude",
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Claude generation failed")
            raise ExternalServiceError(
                f"Claude API call failed: {exc}"
            ) from exc


def get_llm_provider(settings: Settings | None = None) -> LLMProvider:
    """
    Factory that returns the configured LLMProvider implementation.

    This is the single place in the codebase that branches on
    `settings.llm_provider`. Every service depends on the
    `LLMProvider` interface (usually via FastAPI's `Depends`), never
    on this factory's branches directly.
    """
    settings = settings or get_settings()

    if settings.llm_provider == "gemini":
        return GeminiProvider(settings.gemini_api_key, settings.gemini_model_name)
    if settings.llm_provider == "openai":
        return OpenAIProvider(settings.openai_api_key, settings.openai_model_name)
    if settings.llm_provider == "claude":
        return ClaudeProvider(
            settings.anthropic_api_key, settings.anthropic_model_name
        )

    raise ValueError(f"Unknown LLM provider configured: {settings.llm_provider}")
