# Hyttestatus

A remote cabin status portal for Victron VRM telemetry and energy history.

## Project status

**Phase:** single-location MVP  
**Deployment target:** Unraid with Docker Compose  
**Initial installation:** one cabin with a Victron GX system and limited/periodic Starlink connectivity

## Current repository contents

- Initial responsive dashboard page with clearly marked empty/demo states.
- FastAPI application and health endpoint.
- Docker Compose skeleton for web, worker, and PostgreSQL.
- Environment template and gitignore.
- Architecture, security, VRM-integration, MVP, and Unraid deployment notes.

**Important:** this is a development skeleton. Authentication, actual VRM synchronization, database models/migrations and retention are not implemented. Do not expose it publicly or put real credentials into it yet.

## MVP goals

- Show selected Victron VRM metrics with a clear **last updated** timestamp.
- Continue to show locally cached data when the cabin or VRM is offline.
- Provide role-based views:
  - **Guest:** selected high-level status.
  - **Owner:** guest view plus energy trends and battery/solar history.
  - **Installer:** diagnostics, device-level readings and integration health.
- Keep all secrets server-side; never expose VRM credentials to the browser.
- Structure data by location from the beginning, while configuring one location for the initial MVP.

## Proposed architecture

- **Web frontend:** responsive web UI.
- **API:** Python + FastAPI.
- **Database:** PostgreSQL for location metadata, users, telemetry and sync state.
- **VRM sync worker:** scheduled polling/import job; cache results locally.
- **Deployment:** Docker Compose on Unraid.

Avoid exposing Unraid administration or the VRM API token directly to the public internet.

## Repository layout

```text
hyttestatus/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── worker.py
│   │   └── templates/
│   ├── Dockerfile
│   └── requirements.txt
├── deploy/
│   └── docker-compose.yml
├── docs/
│   ├── architecture.md
│   ├── security.md
│   ├── vrm-integration.md
│   ├── mvp-plan.md
│   └── unraid-deployment.md
├── .env.example
├── .gitignore
└── README.md
```

## Unraid quick start

1. Clone the repository on the Unraid host or a suitable development machine.
2. Copy `.env.example` to `.env` and choose strong, unique passwords/secrets.
3. Set `HYTTESTATUS_DB_PATH` to a persistent Unraid directory.
4. Run:

   ```sh
   docker compose -f deploy/docker-compose.yml up -d --build
   ```

5. Check `http://127.0.0.1:8088/health` from the host.

See [docs/unraid-deployment.md](docs/unraid-deployment.md) before deploying.

## Development principles

1. Build and test against one location first.
2. Make offline/stale status explicit; never present old readings as live.
3. Use per-location access control so the project can grow into a hosted multi-customer service.
5. Do not commit credentials, tokens, or production configuration to Git.

## Milestones

1. [x] Initialize repository documentation, architecture, Compose skeleton and dashboard prototype.
3. [ ] Add authentication and role-based access before external use.
4. [ ] Integrate VRM data and local persistence.
5. [ ] Test offline/retry behaviour, backups, and restore.

## Configuration

Copy `.env.example` to a local `.env` file for development. Never commit `.env` or actual secrets.
