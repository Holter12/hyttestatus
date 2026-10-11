from __future__ import annotations

import os
from datetime import datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx

VRM_BASE_URL = "https://vrmapi.victronenergy.com/v2"


class VRMError(RuntimeError):
    """Safe-to-display VRM integration error."""


def configured() -> bool:
    return bool(os.getenv("VRM_API_TOKEN", "").strip() and os.getenv("VRM_INSTALLATION_ID", "").strip())


def _request(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    token = os.getenv("VRM_API_TOKEN", "").strip()
    installation_id = os.getenv("VRM_INSTALLATION_ID", "").strip()
    if not token or not installation_id:
        raise VRMError("VRM API-token eller installasjons-ID mangler.")
    if not installation_id.isdigit():
        raise VRMError("VRM installasjons-ID må være numerisk.")

    url = f"{VRM_BASE_URL}/installations/{installation_id}/{path.lstrip('/')}"
    try:
        response = httpx.get(
            url,
            headers={"X-Authorization": f"Token {token}", "Accept": "application/json"},
            params=params,
            timeout=httpx.Timeout(10.0, connect=5.0),
        )
    except httpx.TimeoutException as exc:
        raise VRMError("Tidsavbrudd ved kontakt med Victron VRM.") from exc
    except httpx.HTTPError as exc:
        raise VRMError("Kunne ikke kontakte Victron VRM.") from exc

    if response.status_code in (401, 403):
        raise VRMError("VRM avviste tilgangen. Kontroller token og tilgang til anlegget.")
    if response.status_code == 429:
        raise VRMError("VRM begrenser forespørsler midlertidig. Prøv igjen senere.")
    if response.status_code >= 500:
        raise VRMError("Victron VRM har en midlertidig serverfeil.")
    if response.status_code >= 400:
        raise VRMError(f"Victron VRM svarte med HTTP {response.status_code}.")
    try:
        payload = response.json()
    except ValueError as exc:
        raise VRMError("Victron VRM returnerte et ugyldig svar.") from exc
    if not isinstance(payload, dict) or payload.get("success") is False:
        raise VRMError("Victron VRM kunne ikke fullføre forespørselen.")
    return payload


def _records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = payload.get("records", [])
    return records if isinstance(records, list) else []


def _find_value(records: list[dict[str, Any]], codes: tuple[str, ...]) -> float | None:
    for item in records:
        if not isinstance(item, dict) or item.get("code") not in codes:
            continue
        raw = item.get("rawValue")
        if raw is None:
            raw = item.get("value")
        try:
            return float(raw)
        except (TypeError, ValueError):
            continue
    return None


def _number(value: Any) -> float | None:
    try:
        parsed = float(value)
        return parsed if parsed >= 0 else None
    except (TypeError, ValueError):
        return None


def _today_energy_totals() -> tuple[float | None, float | None]:
    """Return confirmed solar yield and battery-to-consumer energy for today."""
    timezone_name = os.getenv("TIMEZONE", "Europe/Oslo")
    try:
        site_tz = ZoneInfo(timezone_name)
    except Exception:
        site_tz = ZoneInfo("Europe/Oslo")
    now = datetime.now(site_tz)
    midnight = datetime.combine(now.date(), time.min, tzinfo=site_tz)
    start = int(midnight.timestamp())
    end = int((now + timedelta(minutes=1)).timestamp())
    common = {"interval": "days", "start": start, "end": end}
    solar_payload = _request("stats", {"type": "solar_yield", **common})
    consumption_payload = _request("stats", {"type": "consumption", **common})

    solar_totals = solar_payload.get("totals", {})
    consumption_totals = consumption_payload.get("totals", {})
    solar = _number(solar_totals.get("Pt")) if isinstance(solar_totals, dict) else None
    battery_to_consumers = (
        _number(consumption_totals.get("Bc"))
        if isinstance(consumption_totals, dict) else None
    )
    # VRM returns false for unavailable series. Keep these as None, never as 0.
    return solar, battery_to_consumers


def get_status() -> dict[str, Any]:
    """Read current diagnostic values and today's energy totals from VRM."""
    diagnostics_payload = _request("diagnostics", {"count": 1000})
    diagnostics = _records(diagnostics_payload)
    result: dict[str, Any] = {
        "data_status": "connected",
        "message": "Data hentet fra hyttas GX via Victron VRM.",
        "data_source": "Victron GX via Victron VRM API",
        "battery_soc_percent": _find_value(diagnostics, ("SOC",)),
        "battery_voltage_v": _find_value(diagnostics, ("bv", "V", "voltage")),
        "solar_energy_today_kwh": None,
        "load_energy_today_kwh": None,
        "battery_to_consumers_today_kwh": None,
        "vrm_diagnostic_codes": sorted({
            str(item.get("code")) for item in diagnostics
            if isinstance(item, dict) and item.get("code")
        }),
    }
    try:
        solar, battery_to_consumers = _today_energy_totals()
        result["solar_energy_today_kwh"] = solar
        result["battery_to_consumers_today_kwh"] = battery_to_consumers
    except VRMError:
        # Live battery readings remain useful if the statistics endpoint is unavailable.
        result["message"] = "Batteridata hentet fra hyttas GX via VRM; dagens energistatistikk er foreløpig utilgjengelig."
    return result
