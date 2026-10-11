# Hyttestatus

A remote cabin status portal combining daily camera images, image history, and Victron VRM telemetry.

## Project status

**Phase:** single-location MVP  
**Deployment target:** Unraid with Docker Compose  
**Initial installation:** one cabin with a Victron GX system and limited/periodic Starlink connectivity

## MVP goals

- Show the latest successfully received cabin image and its capture/receipt timestamps.
- Browse image history by date.
- Show selected Victron VRM metrics with a clear **last updated** timestamp.
- Continue to show locally cached data when the cabin or VRM is offline.
- Provide role-based views:
  - **Guest:** latest image, image history and selected high-level status.
  - **Owner:** guest view plus energy trends and battery/solar history.
  - **Installer:** diagnostics, device-level readings and integration health.
- Keep all secrets server-side; never expose VRM credentials to the browser.
- Structure data by location from the beginning, while configuring one location for the initial MVP.

## Proposed architecture

- **Web frontend:** responsive web UI.
- **API:** Python + FastAPI.
- **Database:** PostgreSQL for location metadata, users, telemetry and sync state.
- **Media storage:** persistent filesystem volume, partitioned by location and date.
- **VRM sync worker:** scheduled polling/import job; cache results locally.
- **Deployment:** Docker Compose on Unraid.

The exact image-ingestion method and external access path are still to be decided. Avoid exposing Unraid administration, the camera, or the VRM API token directly to the public internet.

## Suggested repository layout

```text
hyttestatus/
├── backend/
├── frontend/
├── worker/
├── deploy/
│   └── docker-compose.yml
├── docs/
│   ├── architecture.md
│   ├── security.md
│   └── vrm-integration.md
├── .env.example
├── .gitignore
└── README.md
```

## Development principles

1. Build and test against one location first.
2. Make offline/stale status explicit; never present old readings as live.
3. Use per-location access control so the project can grow into a hosted multi-customer service.
4. Keep camera/media access separate from installer-only telemetry.
5. Do not commit credentials, tokens, private images, or production configuration to Git.

## First milestones

1. Confirm repository and deployment assumptions.
2. Add a working Compose skeleton and health checks.
3. Implement a responsive dashboard with clearly labelled demo data.
4. Add secure configuration and user roles.
5. Integrate VRM API data and local persistence.
6. Add image upload/synchronization and date-based gallery.
7. Test offline/retry behaviour and backup/restore.

## Configuration

Copy `.env.example` to a local `.env` file for development. Never commit `.env` or actual secrets.
