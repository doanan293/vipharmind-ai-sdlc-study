"""The frozen price table of prereg-v1 section 7 (USD per 1M tokens, list prices of 2026-11-15)."""

from dataclasses import dataclass

from sdlc_analysis.tokens import ModelTokens


@dataclass(frozen=True)
class Price:
    input: float
    cache_read: float
    cache_write_5m: float
    cache_write_1h: float
    output: float  # includes reasoning/thinking tokens, as the providers bill them


# Gemini and OpenAI charge no cache-write fee: a token written to cache is billed as plain input,
# so their cache-write price equals the input price (their transcripts report 0 writes anyway).
PRICES: dict[str, Price] = {
    "claude-sonnet-5-5": Price(2.00, 0.10, 2.50, 4.00, 10.00),
    "claude-opus-5-5": Price(4.00, 0.20, 5.00, 8.00, 20.00),
    "gemini-3.8-flash-medium": Price(0.75, 0.075, 0.75, 0.75, 3.75),
    "gpt-6-luna": Price(0.10, 0.01, 0.10, 0.10, 0.50),  # calls with <= 272,000 input tokens
    "gpt-6-luna>272k": Price(0.20, 0.02, 0.20, 0.20, 0.75),  # calls with > 272,000 input tokens
}
LONG_CONTEXT = {"gpt-6-luna": "gpt-6-luna>272k"}


def table_model(model: str | None) -> str | None:
    """The table row a served model id belongs to: exact match, else the longest table id the
    model id starts with (dated or suffixed ids such as `claude-sonnet-5-5-20261101` or
    `claude-opus-5-5[1m]`), else None (off-table)."""
    if model is None:
        return None
    if model in PRICES:
        return model
    hits = [k for k in PRICES if ">" not in k and model.startswith(k)]
    return max(hits, key=len) if hits else None


def is_off_table(model: str | None) -> bool:
    """A named model that matches no row of the table. Tokens without a model name (codex does
    not report one) are the cohort's model, not off-table."""
    return model is not None and table_model(model) is None


def price_for(model: str | None, cohort_model: str, long_context: bool = False) -> Price:
    """The table row for `model`; tokens of a model not in the table (or unnamed) are priced as
    the cohort's own model and flagged by the caller (`is_off_table`)."""
    name = table_model(model) or cohort_model
    if long_context:
        name = LONG_CONTEXT.get(name, name)
    return PRICES[name]


def cost_usd(
    tokens: list[ModelTokens], cohort_model: str, long_context: bool = False
) -> float | None:
    """Converted cost of one run; None when no token counts are known."""
    if not tokens:
        return None
    total = 0.0
    for t in tokens:
        p = price_for(t.model, cohort_model, long_context)
        total += (
            t.input_uncached * p.input
            + t.cache_read * p.cache_read
            + t.cache_write_5m * p.cache_write_5m
            + t.cache_write_1h * p.cache_write_1h
            + t.output * p.output
        )
    return total / 1e6
