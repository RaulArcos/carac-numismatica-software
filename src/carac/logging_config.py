import sys
from pathlib import Path

from loguru import logger


LOG_FORMAT_CONSOLE = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

LOG_FORMAT_FILE = (
    "{time:YYYY-MM-DD HH:mm:ss} | "
    "{level: <8} | "
    "{name}:{function}:{line} - "
    "{message}"
)

LOG_LEVEL_CONSOLE = "INFO"
LOG_LEVEL_FILE = "DEBUG"
LOG_ROTATION = "1 day"
LOG_RETENTION = "30 days"
LOG_COMPRESSION = "zip"


def setup_logging() -> None:
    logger.remove()
    
    logger.add(
        sys.stderr,
        format=LOG_FORMAT_CONSOLE,
        level=LOG_LEVEL_CONSOLE,
        colorize=True,
    )
    
    log_dir = Path.home() / ".carac" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        log_dir / "carac_{time:YYYY-MM-DD}.log",
        format=LOG_FORMAT_FILE,
        level=LOG_LEVEL_FILE,
        rotation=LOG_ROTATION,
        retention=LOG_RETENTION,
        compression=LOG_COMPRESSION,
    )
    
    logger.info("Logging configured successfully")