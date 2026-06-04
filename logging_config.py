import logging
import logging.config

from config import config


def setup_logging():
    """
    Configures the logging system based on settings in config.py.
    Creates log directories if they don't exist and sets up rotating file handlers.
    """

    # Ensure the log directory exists
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_file_path = config.LOG_DIR / config.LOG_FILE

    formatter = {
        "format": "%(asctime)s [%(threadName)s] [%(levelname)s]: %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S"
    }

    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "level": config.LOG_LEVEL,
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": config.LOG_LEVEL,
            "formatter": "standard",
            "filename": str(log_file_path),
            "when": "midnight",
            "backupCount": 30,
            "encoding": "utf-8"
        }
    }

    conf_dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"standard": formatter},
        "handlers": handlers,
        "loggers": {},
        "root": {
            "level": config.LOG_LEVEL,
            "handlers": ["console", "file"],
        },
    }

    logging.config.dictConfig(conf_dict)

    root_logger = logging.getLogger()
    root_logger.info("Logging system initialized successfully.")

    return root_logger
