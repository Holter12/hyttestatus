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


def _request(path: str, params: Any = None) -> dict[str, Any]:
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


def get_history(days: int = 14) -> dict[str, Any]:
    """Fetch hourly battery and energy history for the requested recent period."""
    if days < 7 or days > 30:
        raise VRMError("Historikkperioden må være mellom 7 og 30 dager.")
    timezone_name = os.getenv("TIMEZONE", "Europe/Oslo")
    try:
        site_tz = ZoneInfo(timezone_name)
    except Exception:
        site_tz = ZoneInfo("Europe/Oslo")
    now = datetime.now(site_tz)
    start = int((now - timedelta(days=days)).timestamp())
    end = int(now.timestamp())
    params: list[tuple[str, str]] = [
        ("type", "custom"),
        ("interval", "hours"),
        ("start", str(start)),
        ("end", str(end)),
    ]
    for code in ("SOC", "Pb", "Pc", "Bc"):
        params.append(("attributeCodes[]", code))
    payload = _request("stats", params)
    records = payload.get("records", {})
    if not isinstance(records, dict):
        records = {}

    def points(code: str) -> list[dict[str, float | int]]:
        raw_series = records.get(code)
        if not isinstance(raw_series, list):
            return []
        result: list[dict[str, float | int]] = []
        for item in raw_series:
            if not isinstance(item, list) or len(item) < 2:
                continue
            try:
                timestamp = int(item[0])
                value = float(item[1])
            except (TypeError, ValueError):
                continue
            if value < 0:
                continue
            result.append({"timestamp": timestamp, "value": value})
        return result

    series = {code: points(code) for code in ("SOC", "Pb", "Pc", "Bc")}
    return {
        "days": days,
        "timezone": timezone_name,
        "data_source": "Victron GX via Victron VRM API",
        "series": series,
        "counts": {code: len(values) for code, values in series.items()},
    }



def get_tank_history(days: int = 14) -> dict[str, Any]:
    """Return tank level history in liters for a recent period, if VRM has logged it."""
    if days < 7 or days > 30:
        raise VRMError("Historikkperioden må være mellom 7 og 30 dager.")
    timezone_name = os.getenv("TIMEZONE", "Europe/Oslo")
    try:
        site_tz = ZoneInfo(timezone_name)
    except Exception:
        site_tz = ZoneInfo("Europe/Oslo")
    now = datetime.now(site_tz)
    start = int((now - timedelta(days=days)).timestamp())
    end = int(now.timestamp())

    diagnostics = _records(_request("diagnostics", {"count": 1000}))
    tank_records = [
        item for item in diagnostics
        if isinstance(item, dict) and item.get("instance") == 20
    ]
    capacity_m3 = _find_value(tank_records, ("tc",))
    capacity_liters = capacity_m3 * 1000 if capacity_m3 is not None else None

    payload = _request("stats", [
        ("type", "custom"),
        ("interval", "hours"),
        ("start", str(start)),
        ("end", str(end)),
        ("attributeCodes[]", "tl"),
    ])
    records = payload.get("records", {})
    raw_series = records.get("tl") if isinstance(records, dict) else None
    points: list[dict[str, float | int]] = []
    if isinstance(raw_series, list):
        for item in raw_series:
            if not isinstance(item, list) or len(item) < 2:
                continue
            try:
                timestamp = int(item[0])
                level = float(item[1])
            except (TypeError, ValueError):
                continue
            if 0 <= level <= 100:
                points.append({
                    "timestamp": timestamp,
                    "level_percent": level,
                    "liters": level * capacity_liters / 100 if capacity_liters is not None else 0,
                })
    points.sort(key=lambda point: point["timestamp"])
    first = points[0] if points else None
    last = points[-1] if points else None
    difference = (
        float(first["liters"]) - float(last["liters"])
        if first is not None and last is not None and capacity_liters is not None
        else None
    )
    return {
        "days": days,
        "timezone": timezone_name,
        "capacity_liters": capacity_liters,
        "points": points,
        "counts": len(points),
        "start_liters": first["liters"] if first else None,
        "end_liters": last["liters"] if last else None,
        "consumption_liters": difference,
        "note": None if points else "VRM har ikke returnert historiske tanknivåer for perioden.",
    }


def get_advanced_status() -> dict[str, Any]:
    """Return selected live diagnostic fields for battery, MPPT controllers and tank."""
    diagnostics = _records(_request("diagnostics", {"count": 1000}))

    def device(instance: int, title: str) -> dict[str, Any]:
        items = [
            item for item in diagnostics
            if isinstance(item, dict) and str(item.get("instance")) == str(instance)
        ]
        def value(codes: tuple[str, ...]) -> float | None:
            return _find_value(items, codes)
        def label(codes: tuple[str, ...]) -> str | None:
            for item in items:
                if item.get("code") in codes:
                    text = item.get("formattedValue")
                    if text is not None:
                        return str(text)
            return None
        return {
            "title": title,
            "instance": instance,
            "available": bool(items),
            "items": items,
            "voltage_v": value(("bv", "V", "ScV", "PVV")),
            "current_a": value(("I", "ScI", "PVc")),
            "power_w": value(("PVP", "Pdc", "PPV")),
            "temperature_c": value(("ScT", "T")),
            "level_percent": value(("tl",)),
            "remaining_liters": value(("tr",)),
            "capacity_liters": value(("tc",)),
            "status": label(("ts",)),
        }

    battery_items = [
        item for item in diagnostics
        if isinstance(item, dict) and item.get("code") in ("SOC", "bv", "V", "I", "TTG", "CE", "ca")
    ]
    battery = {
        "soc_percent": _find_value(battery_items, ("SOC",)),
        "voltage_v": _find_value(battery_items, ("bv", "V")),
        "current_a": _find_value(battery_items, ("I",)),
        "time_to_go_hours": _find_value(battery_items, ("TTG",)),
        "consumed_ah": _find_value(battery_items, ("CE",)),
        "capacity_ah": _find_value(battery_items, ("ca",)),
    }
    # Keep the complete diagnostic fields for identified devices. Raw records are
    # reduced to safe display fields; API credentials and installation data are never included.
    def display_items(instance: int) -> list[dict[str, Any]]:
        result = []
        for item in diagnostics:
            if not isinstance(item, dict) or str(item.get("instance")) != str(instance):
                continue
            result.append({
                "code": item.get("code"),
                "description": item.get("description"),
                "value": item.get("formattedValue", item.get("rawValue", item.get("value"))),
            })
        return result

    return {
        "data_source": "Victron GX via Victron VRM API",
        "battery": battery,
        "mppt1": {**device(30, "EPEVER Tracer 2210AN"), "items": display_items(30)},
        "mppt2": {**device(277, "Victron MPPT"), "items": display_items(277)},
        "tank": {**device(20, "Tankmåler"), "items": display_items(20)},
    }


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
        "tank_level_percent": _find_value(
            [item for item in diagnostics if isinstance(item, dict) and item.get("instance") == 20],
            ("tl",),
        ),
        "tank_remaining_liters": (
            _find_value(
                [item for item in diagnostics if isinstance(item, dict) and item.get("instance") == 20],
                ("tr",),
            ) * 1000
            if _find_value(
                [item for item in diagnostics if isinstance(item, dict) and item.get("instance") == 20],
                ("tr",),
            ) is not None else None
        ),
        "tank_capacity_liters": (
            _find_value(
                [item for item in diagnostics if isinstance(item, dict) and item.get("instance") == 20],
                ("tc",),
            ) * 1000
            if _find_value(
                [item for item in diagnostics if isinstance(item, dict) and item.get("instance") == 20],
                ("tc",),
            ) is not None else None
        ),
        "tank_status": next(
            (
                str(item.get("formattedValue") or item.get("value"))
                for item in diagnostics
                if isinstance(item, dict) and item.get("instance") == 20 and item.get("code") == "ts"
            ),
            None,
        ),
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


def get_diagnostic_samples() -> list[dict[str, Any]]:
    """Return numeric VRM diagnostics for local time-series storage."""
    diagnostics = _records(_request("diagnostics", {"count": 1000}))
    samples: list[dict[str, Any]] = []
    for item in diagnostics:
        if not isinstance(item, dict):
            continue
        raw = item.get("rawValue")
        if raw is None:
            raw = item.get("value")
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if not (value == value and abs(value) != float("inf")):
            continue
        samples.append({
            "instance": item.get("instance", "unknown"),
            "code": item.get("code"),
            "description": item.get("description"),
            "value": value,
        })
    return samples
