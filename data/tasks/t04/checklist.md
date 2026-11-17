# Checklist t04
Source: hidden tests at f2b898a: backend/tests/infrastructure/test_inline_dispatcher.py, backend/tests/infrastructure/test_settings.py

1. An inline job dispatcher runs the job within the enqueue call itself: enqueue returns only after the job has run.
2. If the job raises, the inline dispatcher retries it (after a configurable delay, which can be zero) until it succeeds.
3. Retries are bounded by a configurable maximum number of runs; when every run fails, it stops after exactly that many runs.
4. A job that keeps failing does not propagate an error to the caller of enqueue (the request that queued it does not fail).
5. Settings accept selecting the inline dispatcher via the environment (PHARMA_JOBS__DISPATCHER=inline), and the loaded settings report dispatcher "inline". [exact]
