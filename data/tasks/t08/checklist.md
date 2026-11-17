# Checklist t08
Source: hidden tests at 8dd6a9c: backend/tests/domain/test_text.py

1. Text normalization converts Unicode to composed form (NFC), so decomposed Vietnamese diacritics become composed.
2. Normalization converts CRLF and lone CR line endings to LF.
3. Normalization strips trailing whitespace on each line, removes leading and trailing blank lines, but keeps leading indentation and interior blank lines.
4. Normalization is idempotent; whitespace-only or empty input becomes an empty string.
5. Snippet creation drops markdown table pipes and separator rows (e.g. "| :--- | ---: |"), joining cell text with single spaces.
6. Snippets collapse runs of whitespace/newlines to single spaces.
7. A snippet longer than the limit is cut at a word boundary and ends with an ellipsis "…", with total length not exceeding the limit.
8. A word that ends exactly at the cut point is kept (e.g. "Paracetamol giảm đau hạ sốt" at 12 gives "Paracetamol…").
9. A single word longer than the limit is hard-cut with an ellipsis (e.g. "Acetylsalicylic" at 8 gives "Acetyls…").
10. Text that already fits is returned trimmed and without an ellipsis.
11. A non-positive character limit is rejected with an error that mentions the limit (max_chars).
