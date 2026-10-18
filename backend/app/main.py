from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.vrm import VRMError, configured as vrm_configured, get_history as get_vrm_history, get_tank_history as get_vrm_tank_history, get_advanced_status as get_vrm_advanced_status, get_status as get_vrm_status\nfrom app.history_store import read_samples as read_local_samples

APP_NAME = os.getenv("APP_NAME", "Hyttestatus")
LOCATION_NAME = os.getenv("DEFAULT_LOCATION_NAME", "Hytte")
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", "/app/media"))

app = FastAPI(
    title=APP_NAME,
    description="Cabin status dashboard — initial single-location MVP",
    version="0.2.0",
)

templates = Jinja2Templates(directory="/app/app/templates")
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(MEDIA_ROOT), check_dir=False), name="media")


def current_status() -> dict[str, object]:
    payload: dict[str, object] = {
        "location": LOCATION_NAME,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_status": "unconfigured",
        "message": "VRM er ikke konfigurert.",
        "battery_soc_percent": None,
        "battery_voltage_v": None,
        "solar_energy_today_kwh": None,
        "load_energy_today_kwh": None,
        "battery_to_consumers_today_kwh": None,
        "latest_image": None,
    }
    if not vrm_configured():
        return payload
    try:
        payload.update(get_vrm_status())
    except VRMError as exc:
        payload["data_status"] = "error"
        payload["message"] = str(exc)
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    return payload


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": APP_NAME}


@app.get("/api/status")
def status() -> dict[str, object]:
    """Return live VRM status, or a clear unavailable state without fake values."""
    return current_status()


@app.get("/api/history")
def history(days: int = Query(default=14, ge=7, le=30)) -> dict[str, object]:
    """Return historical VRM series for 7–30 days."""
    if not vrm_configured():
        raise HTTPException(status_code=503, detail="VRM er ikke konfigurert.")
    try:
        return get_vrm_history(days)
    except VRMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc



@app.get("/api/tank-history")
def tank_history(days: int = Query(default=14, ge=7, le=30)) -> dict[str, object]:
    """Return historical tank levels for 7–30 days."""
    if not vrm_configured():
        raise HTTPException(status_code=503, detail="VRM er ikke konfigurert.")
    try:
        return get_vrm_tank_history(days)
    except VRMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/advanced")
def advanced_status() -> dict[str, object]:
    """Return live values for the advanced energy page."""
    if not vrm_configured():
        raise HTTPException(status_code=503, detail="VRM er ikke konfigurert.")
    try:
        return get_vrm_advanced_status()
    except VRMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/advanced", response_class=HTMLResponse)
def advanced_dashboard(request: Request) -> HTMLResponse:
    try:
        payload = get_vrm_advanced_status() if vrm_configured() else None
        error = None
    except VRMError as exc:
        payload, error = None, str(exc)
    return templates.TemplateResponse(
        request=request,
        name="advanced.html",
        context={"location_name": LOCATION_NAME, "year": datetime.now().year,
                 "advanced": payload, "error": error},
    )

@app.get("/api/vrm/check")
def vrm_check() -> dict[str, object]:
    """Safe connection test: never returns token, installation ID, or raw API data."""
    if not vrm_configured():
        return {"configured": False, "connected": False, "message": "VRM-verdier mangler i miljøet."}
    try:
        result = get_vrm_status()
        return {
            "configured": True,
            "connected": True,
            "message": "Kontakt med Victron VRM fungerer.",
            "available_fields": [
                name for name in (
                    "battery_soc_percent",
                    "battery_voltage_v",
                    "solar_energy_today_kwh",
                    "load_energy_today_kwh",
                    "battery_to_consumers_today_kwh",
                ) if result.get(name) is not None
            ],
        }
    except VRMError as exc:
        return {"configured": True, "connected": False, "message": str(exc)}


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    payload = current_status()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "location_name": LOCATION_NAME,
            "year": datetime.now().year,
            "status": payload,
        },
    )

@app.get("/api/local-history")
def local_history(days: int = Query(default=7, ge=1, le=365)) -> dict[str, object]:
    """Return diagnostic measurements collected locally by the background worker."""
    try:
        return read_local_samples(days)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Lokal historik er ikke tilgjengelig ennå. Kontroller database og worker.") from exc
\n