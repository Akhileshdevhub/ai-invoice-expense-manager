"""The default provider: no LLM call happens, ever.

This is what makes the LLM layer genuinely optional. query_engine.py
already computes the correct numeric answer and a template sentence
before a provider is even consulted — this provider just declines to
rephrase it, so the app returns the template sentence as-is.
"""


class NullProvider:
    @property
    def is_available(self) -> bool:
        return False

    def complete(self, prompt: str) -> str:
        raise RuntimeError("NullProvider cannot complete prompts — check is_available first.")
