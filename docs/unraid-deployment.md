# Unraid deployment (initial skeleton)

This is a development skeleton, not a production-ready public service.

## 1. Prepare storage

Create persistent host directories in your preferred Unraid appdata location, for example:

- `/mnt/user/appdata/hyttestatus/postgres`
- `/mnt/user/appdata/hyttestatus/media`

Ensure the Docker containers can write to these directories. Keep backups outside the same physical storage pool where possible.

## 2. Configure environment

Copy `.env.example` to `.env` in the repository root. Set unique, strong secrets and passwords. Do not commit `.env`.

Add these host paths to `.env`:

```dotenv
HYTTESTATUS_DB_PATH=/mnt/user/appdata/hyttestatus/postgres
HYTTESTATUS_MEDIA_PATH=/mnt/user/appdata/hyttestatus/media
```

## 3. Start services

From the repository root (or configure the equivalent paths in Unraid's Compose Manager):

```sh
docker compose -f deploy/docker-compose.yml up -d --build
```

The web service binds to `127.0.0.1:8088` by default so it is not directly exposed to the LAN/public network. To access it, use a local reverse proxy or change the binding deliberately for a trusted internal network. Do not forward this port directly from your router.

## 4. Check health

```sh
docker compose -f deploy/docker-compose.yml ps
curl http://127.0.0.1:8088/health
```

Expected health response:

```json
{"status":"ok","service":"Hyttestatus"}
```

## Known limitations

- No authentication is implemented yet; do not publish this prototype to the internet.
- VRM integration is not implemented yet.
- Media upload/history API is not implemented yet.
- The worker is a placeholder and does not run scheduled jobs yet.
- Database models/migrations are not implemented yet.
- Configure backups and HTTPS/access controls before using real images or production credentials.
