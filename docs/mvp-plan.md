# MVP plan

## Milestone 1 — Project skeleton

- [x] Create repository documentation and initial architecture.
- [ ] Add Docker Compose and service health checks.
- [ ] Add a basic responsive overview page using clearly marked demo data.
- [ ] Confirm the service starts reliably on Unraid.

## Milestone 2 — One-location dashboard

- [ ] Configure one location from environment or database.
- [ ] Show battery SOC/voltage only when real data is available.
- [ ] Show freshness and offline/stale states.

## Milestone 3 — VRM synchronization

- [ ] Verify API authentication and installation ID.
- [ ] Implement backend-only VRM client.
- [ ] Poll selected, supported metrics and store them locally.
- [ ] Plot recent history.
- [ ] Add tests for API failures and missing device values.

## Milestone 4 — Access control

- [ ] Add secure login and hashed passwords.
- [ ] Enforce guest, owner and installer permissions server-side.
- [ ] Add per-location authorization tests.
- [ ] Verify media links do not bypass authorization.

## Milestone 5 — Pilot readiness

- [ ] Configure HTTPS/private access.
- [ ] Document Unraid deployment and upgrades.
- [ ] Add database/media backup and restore steps.
- [ ] Test a missed Starlink window, partial upload and delayed VRM data.
