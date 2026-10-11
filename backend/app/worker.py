"""Background worker entry point.

VRM synchronization and media retry logic will be added once endpoints and
site upload strategy have been confirmed. This placeholder deliberately does
not poll or contact external services.
"""
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hyttestatus.worker")


def main() -> None:
    logger.info("Hyttestatus worker started; no jobs configured yet.")
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
