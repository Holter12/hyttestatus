from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

APP_NAME = os.getenv("APP_NAME", "Hyttestatus")
LOCATION_NAME = os.getenv("DEFAULT_LOCATION_NAME", "Hytte")
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", "/app/media"))

app = FastAPI(
    title=APP_NAME,
    description="Cabin status dashboard — initial single-location MVP",
    version="0.1.0",
)

templates = Jinja2Templates(directory="/app/app/templates")
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(MEDIA_ROOT), check_dir=False), name="media")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": APP_NAME}


@app.get("/api/status")
def status() -> dict[str, object]:
    """Starter payload. VRM integration replaces unavailable values later."""
    return {
        "location": LOCATION_NAME,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_status": "demo",
        "message": "VRM integration not configured yet",
        "battery_soc_percent": None,
        "battery_voltage_v": None,
        "solar_energy_today_kwh": None,
        "load_energy_today_kwh": None,
        "latest_image": None,
    }


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "location_name": LOCATION_NAME,
            "year": datetime.now().year,
        },
    )
