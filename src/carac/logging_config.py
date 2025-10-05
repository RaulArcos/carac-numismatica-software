import sys
from pathlib import Path

from loguru import logger


class LoggingConfig:
    FORMAT_CONSOLE = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    FORMAT_FILE = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )
    
    LEVEL_CONSOLE = "INFO"
    LEVEL_FILE = "DEBUG"
    ROTATION = "1 day"
    RETENTION = "30 days"
    COMPRESSION = "zip"
    LOG_FILE_PATTERN = "carac_{time:YYYY-MM-DD}.log"
    LOG_DIR_NAME = ".carac"
    LOG_SUBDIR = "logs"


def setup_logging() -> None:
    logger.remove()
    
    logger.add(
        sys.stderr,
        format=LoggingConfig.FORMAT_CONSOLE,
        level=LoggingConfig.LEVEL_CONSOLE,
        colorize=True,
    )
    
    log_dir = Path.home() / LoggingConfig.LOG_DIR_NAME / LoggingConfig.LOG_SUBDIR
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        log_dir / LoggingConfig.LOG_FILE_PATTERN,
        format=LoggingConfig.FORMAT_FILE,
        level=LoggingConfig.LEVEL_FILE,
        rotation=LoggingConfig.ROTATION,
        retention=LoggingConfig.RETENTION,
        compression=LoggingConfig.COMPRESSION,
    )
    
    logger.info("Logging configured successfully")