import sys
from pathlib import Path

from loguru import logger


def setup_logging() -> None:
    logger.remove()

    if sys.stderr is not None:
        logger.add(
            sys.stderr,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            ),
            level="WARNING",
            colorize=True,
        )

    log_dir = Path.home() / ".carac" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_dir / "carac_{time:YYYY-MM-DD}.log",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
            "{name}:{function}:{line} - {message}"
        ),
        level="INFO",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        enqueue=True,
    )

    logger.info("Logging configured successfully")