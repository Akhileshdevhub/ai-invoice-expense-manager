"""Provider interface for the optional LLM layer.

Any provider just needs to turn a prompt into text. Kept as a tiny
Protocol rather than an elaborate plugin system — there are two
implementations (null and OpenAI) and that's the actual requirement.
"""

from typing import Protocol


class LLMProvider(Protocol):
    def complete(self, prompt: str) -> str:
        """Return a text completion for the given prompt."""
        ...

    @property
    def is_available(self) -> bool:
        """False when the provider has no way to actually call an LLM (e.g. no API key)."""
        ...
