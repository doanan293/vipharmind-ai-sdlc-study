Let publish jobs run inside the request that queued them, for serverless hosts that may freeze a function once it has answered.
Add a class `InlineDispatcher` in `pharma_agent.infrastructure.jobs.inline`, constructed as `InlineDispatcher(run, *, retry_delay_seconds=2.0, max_runs=3)` where `run` is an async callable taking a job id.
Its async method `enqueue(job_id)` must return only after the job has run successfully or has used all of its runs.
When `run` raises, the dispatcher waits briefly and calls it again, up to `max_runs` calls in total.
A job that keeps failing must not make `enqueue` raise, so the publish request still succeeds.
Accept `inline` as a value of the `jobs.dispatcher` setting (environment variable `PHARMA_JOBS__DISPATCHER`), select this dispatcher for publishing when it is configured, and treat it like `inprocess` for internal call authentication.
Also expose a module-level ASGI `app` in `pharma_agent.api.asgi` for hosts that import an application object instead of running the server command.
