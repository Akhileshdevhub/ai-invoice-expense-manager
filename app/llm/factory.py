"""Pick an LLM provider based on environment configuration.

The only place in the app that decides *which* provider to use — the
rest of the app just calls provider.is_available / provider.complete().
"""

import os

from app.llm.providers.null_provider import NullProvider


def get_default_provider():
    if os.environ.get("OPENAI_API_KEY"):
        from app.llm.providers.openai_provider import OpenAIProvider
        return OpenAIProvider()
    return NullProvider()
