# Victron VRM integration

## Goal

Import selected VRM data for the initial GX installation, persist it locally, and serve cached readings to the dashboard. The dashboard must continue to work when the cabin, Starlink, or VRM is temporarily unavailable.

## Before implementation

- Confirm the current VRM API authentication method and endpoints against the official VRM API documentation.
- Confirm the target installation identifier and which endpoints expose the required telemetry and energy statistics.
- Request the minimum permissions needed by the integration.
- Store the token only in backend environment/secrets configuration.

## Initial metrics to evaluate

- Battery state of charge (SOC), if exposed by the installation's battery monitor.
- Battery voltage and current.
- Solar charge power and daily yield for supported chargers.
- AC/DC consumption or system power where available.
- Tank level only if the VRM API exposes a useful value for the listed tank device.
- Device online/last-seen status, if exposed.

Exact metric availability varies by device and VRM data source. Do not assume all metrics exist; handle missing metrics gracefully.

## Polling strategy

- Poll conservatively; use VRM timestamps and limits documented by Victron.
- Prefer suitable historical/statistics endpoints over repeatedly pulling high-resolution graph data.
- Record source timestamps and fetched timestamps.
- Upsert telemetry samples to avoid duplicates.
- Record sync failures without writing credentials or sensitive responses to logs.
- Show a visible "last updated" label for every summary panel.

## Acceptance criteria

- A failed VRM request does not make the dashboard unavailable.
- Existing readings remain available with an accurate stale-data indicator.
- API token never appears in client-side JavaScript, page source or unauthenticated responses.
- Automated tests cover missing metrics, rate-limit/error responses and timestamp handling.
