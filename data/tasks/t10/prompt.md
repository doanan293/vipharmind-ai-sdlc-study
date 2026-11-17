Wire user authentication with fastapi-users into the infrastructure layer, in a new module `pharma_agent.infrastructure.auth.users`.
Provide `build_auth(settings: AuthSettings, resolve_sessions)` that returns an `Auth` object, where `resolve_sessions` is a callable taking the request and returning an async SQLAlchemy session factory for the existing user and OAuth account tables.
The object exposes the configured `FastAPIUsers` instance, a JWT bearer authentication backend whose token URL is `/api/v1/auth/jwt/login` and whose lifetime comes from the settings, a dependency for the current active user, and a `google` attribute.
`google` is a Google OAuth2 client when Google sign-in is enabled with a client id and secret, and `None` otherwise.
When no JWT secret is configured, `build_auth` must fail immediately with the existing settings error that names `PHARMA_AUTH__JWT_SECRET`.
Provide `include_auth_routes(router, auth)` that mounts the login and logout routes under `/auth/jwt`, registration under `/auth` (giving `/auth/register`), the user routes under `/users` (including `/users/me`), and, only when Google is configured, the OAuth authorize and callback routes under `/auth/google`.
The Google callback must redirect to `<frontend_url>/auth/google/callback`, link accounts by email and mark new Google users as verified.
