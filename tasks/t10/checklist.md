# Checklist t10
Source: hidden tests at 44466f3: backend/tests/infrastructure/test_auth_wiring.py

1. With a JWT secret configured, the auth wiring mounts a JWT login route at /auth/jwt/login and logout at /auth/jwt/logout (relative to the router it is mounted on).
2. User registration is mounted at /auth/register.
3. Current-user routes are mounted under /users, including /users/me.
4. When Google sign-in is not configured, no /auth/google routes are mounted and no Google OAuth client is created.
5. When Google client id, client secret and frontend URL are configured, Google OAuth authorize and callback routes are mounted at /auth/google/authorize and /auth/google/callback.
6. Building the auth wiring without a JWT secret fails immediately with an error that names the PHARMA_AUTH__JWT_SECRET setting.
