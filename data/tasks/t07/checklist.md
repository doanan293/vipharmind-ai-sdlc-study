# Checklist t07
Source: hidden tests at cd9ce58: backend/tests/domain/test_conversation_context.py, backend/tests/domain/test_skill.py

1. The context built for rephrasing a follow-up question excludes turns whose status is blocked, error or timeout, keeping only completed turns.
2. Of the remaining turns, only the most recent N (configurable) are kept, in chronological order, and the conversation summary is passed through.
3. When the kept turns exceed a character budget, the oldest turns are dropped until the context fits.
4. A summary longer than the character budget is cut to exactly the budget; the context reports itself non-empty when it has a summary, and empty when it has neither summary nor turns.
5. A skill markdown file with YAML frontmatter (name, description) and a "## Tìm kiếm" (search) section and a "## Trả lời" (answer) section parses into name, description, search guidance and answer guidance (section bodies trimmed). [exact]
6. A parsed skill gets a content-derived version string of 12 characters. [exact]
7. A skill with only one of the two guidance sections is accepted (the missing one is empty); a skill with neither section is rejected.
8. Skill markdown is rejected when frontmatter is missing, lacks description, has unknown extra keys, or has an empty name.
9. Resolving a list of selected skill ids drops ids not in the catalog, removes duplicates, keeps the requested order, and caps the result at a configurable maximum.
10. A skill can be projected to its metadata (id, name, description) and to the selected-skill form carrying its guidance.
11. Skill ids must be lowercase slug-style; an id like "Bad_Id" is rejected.
