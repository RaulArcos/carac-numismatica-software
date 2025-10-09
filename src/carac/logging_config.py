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

    @classmethod
    def get_log_directory(cls) -> Path:
        return Path.home() / cls.LOG_DIR_NAME / cls.LOG_SUBDIR


def setup_logging() -> None:
    logger.remove()

    _configure_console_logging()
    _configure_file_logging()

    logger.info("Logging configured successfully")


def _configure_console_logging() -> None:
    logger.add(
        sys.stderr,
        format=LoggingConfig.FORMAT_CONSOLE,
        level=LoggingConfig.LEVEL_CONSOLE,
        colorize=True,
    )


def _configure_file_logging() -> None:
    log_dir = LoggingConfig.get_log_directory()
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_dir / LoggingConfig.LOG_FILE_PATTERN,
        format=LoggingConfig.FORMAT_FILE,
        level=LoggingConfig.LEVEL_FILE,
        rotation=LoggingConfig.ROTATION,
        retention=LoggingConfig.RETENTION,
        compression=LoggingConfig.COMPRESSION,
    )