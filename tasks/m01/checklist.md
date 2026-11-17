# Checklist m01
Source: hidden tests at 507a4ae: backend/tests/domain/corpus/test_bundle_io.py, backend/tests/domain/corpus/test_identity.py

1. A knowledge bundle (manifest, documents, sections with blocks, glossary, colloquial mappings, embeddings per model) can be written to a directory and read back, yielding an equal bundle (with the computed manifest).
2. The bundle directory stores documents and sections one record per line (JSON Lines, Vietnamese text written unescaped), glossary and colloquial mappings as JSON lists, and one embeddings file per embedding model.
3. Writing computes the manifest from the content: document count, section count, a listing of every written file with its SHA-256 digest and byte size, and one embedding entry per model with its vector dimension and file; placeholder/stale values in the input manifest are replaced.
4. A bundle without embeddings writes no embeddings folder, lists no embedding files/entries in the manifest, and reads back with empty embeddings.
5. Writing the same bundle twice produces identical manifests and byte-identical files (deterministic output).
6. Writing validates content first and refuses to write anything (no manifest) if there are problems, reporting all of them at once (e.g. a duplicate document key and an embedding model whose vectors have different lengths).
7. Reading reports every problem of an invalid bundle at once (not just the first), each problem naming the file, the 1-based line or list index where applicable, and the field path.
8. A missing manifest is reported as such (and stops reading); a manifest with an unsupported schema version is rejected (only the v1 schema is accepted).
9. Reading verifies each listed file against the manifest: size mismatch, SHA-256 mismatch, missing file, and files listed that are not part of the bundle format are each reported.
10. Manifest document/section counts that do not match the actual number of records are reported.
11. Invalid record fields are reported with their line (e.g. an unknown document kind; valid kinds are drug monograph, general monograph, leaflet).
12. Sections referencing an unknown document are reported.
13. Duplicate section keys and duplicate section ordinals within the same document are reported, pointing at the first occurrence's line.
14. Page ranges are validated: pages must be >= 1 and start page must not be after end page, for sections and for blocks.
15. Sections must have at least one block, and block markdown must not be empty/blank.
16. Colloquial mappings must reference existing sections, and a section can belong to at most one mapping (a second mapping of the same section is reported, naming the earlier mapping); a mapping key may be empty or a slug.
17. Glossary entries must have a term (missing term is a validation problem); blank terms and terms duplicated case-insensitively are reported, pointing at the first occurrence.
18. Embedding lines are validated: dims must match the manifest's dims for that model, vector byte length must equal dims x 4 (float32), hashes must be 64-char lowercase hex SHA-256, and duplicate hashes in a file are reported.
19. Manifest embedding entries must have dims >= 1 and point at the expected file for their model.
20. A fixed, pinned corpus UUID namespace is used for deterministic ids.
21. Canonical JSON serialization sorts keys, is compact, keeps non-ASCII text, and normalizes strings (NFC, line endings, trailing whitespace) before serialization; a SHA-256 hex helper hashes UTF-8 text.
22. A section revision id is a deterministic UUID derived from the section key and its blocks' content: identical for equal content (and for content differing only in trailing whitespace/CRLF), different when a page number, block order, or section key changes.
23. A chunk version id is a deterministic UUID derived from section key, chunk text, embedding text and chunker version: it changes when any of them changes, but not for whitespace/line-ending-only differences.
