"""Background worker for periodic VRM history collection."""
from __future__ import annotations

import logging
import os
import time

from app.history_store import init_db, save_samples
from app.vrm import VRMError, configured, get_diagnostic_samples

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hyttestatus.worker")


def collect_once() -> int:
    if not configured():
        logger.warning("VRM is not configured; skipping history sample.")
        return 0
    samples = get_diagnostic_samples()
    saved = save_samples(samples)
    logger.info("Stored %s VRM diagnostic values from %s available fields.", saved, len(samples))
    return saved


def main() -> None:
    interval = max(60, int(os.getenv("VRM_POLL_INTERVAL_SECONDS", "300")))
    while True:
        try:
            init_db()
            collect_once()
        except (VRMError, RuntimeError, OSError) as exc:
            logger.warning("History collection failed: %s", exc)
        except Exception:
            logger.exception("Unexpected history collection failure")
        time.sleep(interval)


if __name__ == "__main__":
    main()
