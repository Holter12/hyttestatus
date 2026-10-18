"""Persistent sampled VRM diagnostic history in PostgreSQL."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

_engine: Engine | None = None


def engine() -> Engine:
    global _engine
    if _engine is None:
        url = os.getenv("DATABASE_URL", "").strip()
        if not url:
            raise RuntimeError("DATABASE_URL er ikke konfigurert")
        _engine = create_engine(url, pool_pre_ping=True, future=True)
    return _engine


def init_db() -> None:
    with engine().begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vrm_samples (
                id BIGSERIAL PRIMARY KEY,
                sampled_at TIMESTAMPTZ NOT NULL,
                instance TEXT NOT NULL,
                code TEXT NOT NULL,
                description TEXT,
                value DOUBLE PRECISION NOT NULL,
                UNIQUE (sampled_at, instance, code)
            )
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_vrm_samples_instance_time
            ON vrm_samples (instance, sampled_at)
        """))


def save_samples(samples: list[dict[str, Any]], sampled_at: datetime | None = None) -> int:
    """Persist numeric diagnostic values; duplicate samples are ignored."""
    timestamp = sampled_at or datetime.now(timezone.utc)
    rows = []
    for item in samples:
        try:
            value = float(item.get("value"))
            if value != value or value in (float("inf"), float("-inf")):
                continue
            code = str(item.get("code") or "").strip()
            instance = str(item.get("instance") if item.get("instance") is not None else "unknown")
            if not code:
                continue
            rows.append({
                "sampled_at": timestamp,
                "instance": instance,
                "code": code,
                "description": str(item.get("description") or "")[:500],
                "value": value,
            })
        except (TypeError, ValueError):
            continue
    if not rows:
        return 0
    with engine().begin() as conn:
        result = conn.execute(text("""
            INSERT INTO vrm_samples (sampled_at, instance, code, description, value)
            VALUES (:sampled_at, :instance, :code, :description, :value)
            ON CONFLICT (sampled_at, instance, code) DO NOTHING
        """), rows)
    return result.rowcount or 0


def read_samples(days: int = 7) -> dict[str, Any]:
    init_db()
    with engine().connect() as conn:
        rows = conn.execute(text("""
            SELECT sampled_at, instance, code, description, value
            FROM vrm_samples
            WHERE sampled_at >= now() - (:days * interval '1 day')
            ORDER BY sampled_at ASC
        """), {"days": days}).mappings().all()
    series: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for row in rows:
        instance = str(row["instance"])
        code = str(row["code"])
        series.setdefault(instance, {}).setdefault(code, []).append({
            "timestamp": int(row["sampled_at"].timestamp()),
            "value": row["value"],
        })
    return {
        "days": days,
        "sampling_interval_minutes": int(os.getenv("VRM_POLL_INTERVAL_SECONDS", "300")) // 60,
        "data_source": "Lokalt lagrede VRM-diagnostikkmålinger",
        "sample_count": len(rows),
        "latitude": float(os.getenv("LATITUDE")) if os.getenv("LATITUDE") else None,
        "longitude": float(os.getenv("LONGITUDE")) if os.getenv("LONGITUDE") else None,
        "series": series,
    }
