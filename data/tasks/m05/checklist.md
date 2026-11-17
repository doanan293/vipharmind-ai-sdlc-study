# Checklist m05
Source: hidden tests at adf89a7: backend/tests/application/test_import_bundle.py, backend/tests/application/test_release_service.py

1. Importing a knowledge bundle into a collection creates a new release (number 1 for a new collection) that ends in status READY with its ready time set; without publishing, it is not published and the collection's current release stays unset.
2. Embedding vectors for chunk texts are resolved in priority order: the embedding cache first, then vectors shipped in the bundle, then the embedder for the rest; release stats count cached, from-bundle and computed embeddings separately.
3. Only texts missing from both cache and bundle are sent to the embedder, in batches no larger than the configured batch size; all resolved vectors end up in the cache.
4. Every chunk of the release is written to the vector index tagged with the release id; release stats record chunk count, points upserted and points updated.
5. Importing with publish makes the release the collection's current release and sets its published time.
6. Re-importing an identical bundle that is already published reports "no change", returns the same release, and does no staging, index setup or embedding work.
7. Re-importing an identical bundle whose release is READY but unpublished reuses that release (reported as reused) and publishes it if asked, without creating a second release.
8. If embedding fails mid-import, the release is left in BUILDING (not current), vectors already computed stay cached, and rerunning the import resumes the same release, only embedding the missing texts, then becomes READY and published.
9. Importing a changed bundle creates the next release number; unchanged chunks get the new release id added to their index points (counted as updated), new chunks are inserted with only the new release id, removed chunks keep only the old release id; only new texts are embedded; publishing makes it current.
10. Bundle vectors declared with a dimension different from the embedding model's are ignored and recomputed.
11. A bundle vector with the wrong length is rejected (error mentioning dims) before anything is written (no staging, no index setup).
12. If the vector index ends up missing expected points after writing, the import fails (error mentions the expected points) and the release stays BUILDING.
13. Embedding work respects a maximum concurrency limit, and a non-positive batch size is rejected.
14. Listing releases of a collection returns newest first with a flag marking the current one; listing without a collection returns releases across all collections.
15. Publishing a READY release by id makes it current and sets its published time; publishing a BUILDING release is refused (error mentions "building"); publishing an unknown release id is "release not found".
16. Rollback points the collection back to the previously published release; rolling back again with no earlier published release is refused; after re-publishing the newer release, rollback works again; rolling back an unknown collection is "collection not found".
17. Garbage collection with "keep N" retires older non-current releases (newest first in its report), removes their release ids from index points, deletes points no longer used by any kept release, and reports points deleted and updated.
18. Retired releases show status RETIRED with zero chunks; the current release stays READY and current.
19. GC purges unreferenced chunk versions from storage but keeps chunk versions that are still protected (e.g. cited by messages), reporting kept vs deleted counts.
20. Running GC again is idempotent: nothing more is retired, updated or deleted.
21. Reindex rebuilds the vector index for a collection from stored releases and cached vectors: every chunk is upserted with all the release ids that contain it, and per-release point counts are reported.
22. Reindex skips releases built with a different embedding model (reported as skipped) and re-embeds only texts whose vectors are missing from the cache.
