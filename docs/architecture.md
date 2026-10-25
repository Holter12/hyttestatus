# Architecture (MVP)

## Runtime components

- `web/api`: serves the UI and authenticated API.
- `worker`: scheduled jobs such as VRM polling.
- `db`: durable relational state.

For the first iteration, prefer a small number of containers and straightforward operations over premature microservices. The web/API and background worker can share the same codebase and image while running as separate Compose services.

## Data flow

1. The worker retrieves allowed VRM telemetry and persists values with source timestamps and retrieval timestamps.
2. The UI reads cached data from the local database.
3. Pages display data freshness explicitly, e.g. `Last received 6 hours ago`.

## Core entities

- `Location`: site name, slug, timezone, status.
- `User`: login identity and active state.
- `LocationMembership`: user, location and role (`guest`, `owner`, `installer`).
- `TelemetrySample`: location, device/source, metric key, value, unit, source timestamp, fetched timestamp.
- `SyncRun`: integration, started/finished timestamps, status and non-secret error summary.

## Access boundaries

- Guests can see only approved high-level metrics.
- Owners can see owner-level energy history and site status.
- Installers can see diagnostics for locations assigned to them.
- Every location-scoped API query must enforce membership on the server.
- Secret tokens must remain on the backend and must not be included in JSON responses or logs.

## Reliability

- Store source timestamps and retrieval timestamps separately.
- Display stale/offline states rather than implying current values.

## Deployment

Use named volumes or explicitly configured Unraid host paths for PostgreSQL. Back up the database regularly. Keep the service behind a trusted reverse proxy or private access layer; never expose the Unraid management interface.
