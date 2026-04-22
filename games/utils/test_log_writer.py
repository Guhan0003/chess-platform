import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from django.conf import settings


def get_testing_timer_logger() -> logging.Logger:
    """
    Dedicated logger for high-frequency timer polling diagnostics.
    Writes to testing_logs/timer/timer_polling.log to keep terminal clean.
    """
    logger = logging.getLogger("games.testing.timer")
    if logger.handlers:
        return logger

    logs_dir = Path(settings.BASE_DIR) / "testing_logs" / "timer"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "timer_polling.log"

    handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))

    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False
    return logger

