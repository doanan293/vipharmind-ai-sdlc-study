Add shared text helpers to the domain layer in a new module `pharma_agent.domain.shared.text`.
Provide `normalize_text(text: str) -> str`, which converts the text to Unicode NFC, turns every `\r\n` or lone `\r` into a line break, strips trailing whitespace from each line, and removes blank lines at the start and end while keeping inner blank lines and leading indentation.
It must be idempotent and return an empty string for empty or whitespace-only input.
Provide `make_snippet(text: str, max_chars: int) -> str`, which builds a one-line preview: Markdown table separator rows are dropped, table pipes are removed, and all whitespace runs collapse to single spaces with the ends trimmed.
If the result fits in `max_chars` it is returned unchanged; otherwise it is cut at the last word boundary so that the kept words plus a trailing `…` fit within `max_chars`, keeping a word that ends exactly at the cut.
When a single word is longer than the limit, the word itself is cut so that the text plus `…` is exactly `max_chars` characters.
A `max_chars` of zero or less raises `ValueError` with a message that mentions `max_chars`.
