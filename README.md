# Optimal Build

## Frontend environment configuration

The frontend reads API locations from the `VITE_API_BASE_URL` variable that is loaded by Vite at build time. The value is resolved with `new URL(path, base)` so that links behave correctly whether the backend is exposed on the same origin, via a sub-path proxy, or through a separate host. For local development we provide a default of `/` in `frontend/.env` (copy `frontend/.env.example`) so the app talks to whichever host serves the frontend.

### Configuring `VITE_API_BASE_URL`

| Environment | Suggested value | Notes |
|-------------|-----------------|-------|
| Local development with Vite proxy or reverse proxy | `/` | Default value. Requests are routed relative to the web origin, allowing a dev proxy (e.g., Vite's `server.proxy`) or an ingress controller to forward traffic to the API service. |
| Local development without a proxy | `http://localhost:8000/` | Point directly at the backend when running it on a different host/port than the frontend dev server. |
| Staging/production behind a proxy prefix | `/api/` (or another sub-path) | Useful when a load balancer terminates TLS and exposes the API under a path prefix on the same domain as the UI. |
| Staging/production on a dedicated API domain | `https://api.example.com/` | Use a fully-qualified URL when the API is hosted on a different domain. |

Set the variable in the environment that builds the frontend (e.g., `frontend/.env`, `.env.production`, Docker/CI environment variables, or hosting provider settings). Because the variable name starts with `VITE_`, it is inlined at build time and no additional runtime configuration is required.
