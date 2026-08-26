# LLM Architecture

## The rule: the LLM never computes a number

Every figure this app ever shows — a dashboard total, a category
breakdown, an insight sentence, or the answer to a typed question —
is produced by `app/analytics` running a pandas aggregation directly
against confirmed rows in SQLite. The LLM, when one is configured, is
only ever used for two things, both downstream of that computation:

1. **Parsing an ambiguous typed question into a structured intent**
   (which category, which date range, which metric) — and even this
   step is not LLM-based in the current implementation; see below.
2. **Rewording an already-computed answer** in more natural language.

This ordering is enforced by the code structure, not just a convention:
`app/llm/query_engine.py::answer_query()` calls
`app/llm/query_parser.py::parse_query()` and `app/analytics` to get
`result_value` and `template_answer` *before* it ever touches a
provider. The LLM call, if it happens, receives the already-correct
answer as a fact in the prompt ("do not alter the numbers") and is asked
only to rephrase it — see `_reword_with_llm()`.

## Why the intent parser is rule-based, not an LLM call

`app/llm/query_parser.py` uses keyword/regex matching (including a small
Hindi/Hinglish keyword table) to turn a question like
*"Maine last month food pe kitna spend kiya?"* into
`QueryIntent(metric="category_total", category="Food", date_range="last_month")`.

This was a deliberate choice over calling an LLM to do the parsing:

- **It works with zero API keys.** The product brief for this app
  explicitly requires the core features (including natural-language
  querying) to function without any LLM configured — a rule-based parser
  is what makes that possible for this feature specifically, not just
  for the dashboard.
- **The five example questions in the product brief are all answerable
  by matching a bounded set of keywords** (a metric word, a category
  word, a date-range phrase). An LLM-based intent parser would be solving
  a harder, more general problem than this app actually has.
- **Debuggability.** A wrong parse is traceable to a specific regex not
  matching (see `tests/test_query_parser.py`), rather than an opaque
  model decision that would need its own separate evaluation.

The tradeoff is real and worth stating plainly: this parser only
understands the keywords it's been given (`CATEGORY_KEYWORDS`,
`MONTH_NAMES`, and the metric/date-range pattern lists in
`query_parser.py`). A genuinely novel phrasing outside that vocabulary
falls back to the defaults (`total_spending`, `this_month`) rather than
failing — which is safer than guessing wrong, but it does mean the
parser has a real, documented ceiling. Swapping in an LLM-based parser
*for the intent-extraction step only* (while keeping the "LLM never
computes the number" rule) is a reasonable future extension — see
`docs/LIMITATIONS.md`.

## Provider architecture

```
app/llm/base.py                    LLMProvider protocol: complete(prompt) -> str, is_available
app/llm/providers/null_provider.py  default; is_available == False, always
app/llm/providers/openai_provider.py  used only if OPENAI_API_KEY is set
app/llm/factory.py                  reads the environment, returns the right provider
```

`get_default_provider()` is the only place that decides which provider to
use. Everything else in the app depends only on the `LLMProvider`
interface, so adding a third provider (Anthropic, a local model via
Ollama, etc.) means writing one new file that implements `complete()` and
`is_available`, and adding one branch to the factory — no changes
anywhere else.

## Fallback behavior

- **No `OPENAI_API_KEY` set**: `get_default_provider()` returns
  `NullProvider`, `is_available` is `False`, and `answer_query()` never
  attempts a completion — `final_answer` is just `template_answer`. This
  is the default state of this repository (see `.env.example`) and is
  fully tested (`tests/test_query_engine.py::test_null_provider_means_template_answer_is_final_answer`).
- **Key set but the API call fails** (network issue, invalid key, rate
  limit): `answer_query()` catches the exception and falls back to
  `template_answer` rather than raising — the user still gets a correct,
  if less naturally phrased, answer. See the `try/except` around
  `_reword_with_llm()` in `query_engine.py`.

## What wasn't built, and why

This project's LLM key was not available during development (see
`docs/LIMITATIONS.md`), so `OpenAIProvider` is implemented against the
documented OpenAI chat completions API shape but has not been exercised
against a live key in this environment. The `NullProvider` path — which
is what every dashboard figure, insight, and query answer in this
repository's screenshots was produced with — has been fully tested and
run.
