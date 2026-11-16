# Checklist t12
Source: hidden tests at 94a54f8: backend/tests/infrastructure/test_filesystem_catalog.py

1. The repository ships system skill playbooks (one SKILL.md per folder in the backend skills directory) with exactly the ids brand-to-generic, dosing-by-population, drug-interaction, drug-monograph and plain-language. [exact]
2. Loading the skills directory produces one skill per folder, with the folder name as the skill id.
3. Loaded system skills have no owner and are enabled.
4. Every shipped skill has non-empty search guidance and non-empty answer guidance.
5. No shipped skill's guidance contains the "does not replace a doctor/pharmacist" disclaimer (Vietnamese phrase "không thay thế", case-insensitive).
6. A filesystem-backed skill catalog lists skill metadata (with non-empty descriptions), honoring the requested limit.
7. Fetching skills by id returns the known skills and silently ignores unknown ids.
8. A skill folder whose name is not a valid skill id (e.g. "Bad_Name") makes loading fail loudly instead of being skipped.
