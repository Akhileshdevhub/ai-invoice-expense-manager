"""OpenAI-backed provider. Only instantiated when OPENAI_API_KEY is set.

Import of the `openai` package is deferred into __init__ so that an
environment with no LLM configured (and the package not installed)
doesn't need it at all — see docs/LLM_ARCHITECTURE.md.
"""

import os


class OpenAIProvider:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self._client = None

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    def complete(self, prompt: str) -> str:
        if not self.is_available:
            raise RuntimeError("OpenAIProvider has no API key configured.")
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI  # deferred import, see module docstring
            self._client = OpenAI(api_key=self.api_key)
        return self._client
