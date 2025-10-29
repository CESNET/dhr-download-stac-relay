import sys
import re
import os
import logging, logging.config

from logging.handlers import TimedRotatingFileHandler

from pathlib import Path

from sanic_server import SanicServer

import env

def setup_logging(current_path):
    if env.LOGGER__LOG_DIRECTORY[0] == '/':
        log_dir = Path(env.LOGGER__LOG_DIRECTORY)
    else:
        log_dir = os.path.join(current_path, env.LOGGER__LOG_DIRECTORY)
    log_file = os.path.join(str(log_dir), env.LOGGER__LOG_FILENAME)

    Path(str(log_dir)).mkdir(parents=True, exist_ok=True)

    logger_http_server = logging.getLogger(env.LOGGER__NAME)
    logger_http_server.setLevel(env.LOGGER__LOG_LEVEL)

    log_format = logging.Formatter("%(asctime)s [%(threadName)s] [%(levelname)s]: %(message)s")

    rotating_info_handler = TimedRotatingFileHandler(log_file, when="midnight")
    rotating_info_handler.setFormatter(log_format)
    rotating_info_handler.setLevel(env.LOGGER__LOG_LEVEL)
    rotating_info_handler.suffix = "%Y%m%d%H%M%S"
    rotating_info_handler.extMatch = re.compile(r"^\d{14}$")
    logger_http_server.addHandler(rotating_info_handler)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(env.LOGGER__LOG_LEVEL)
    stdout_handler.setFormatter(log_format)
    logger_http_server.addHandler(stdout_handler)

    return logger_http_server

def setup_logging_config(current_root):
    if env.LOGGER__LOG_DIRECTORY[0] == '/':
        log_dir = Path(env.LOGGER__LOG_DIRECTORY)
    else:
        log_dir = Path(current_root) / env.LOGGER__LOG_DIRECTORY

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / env.LOGGER__LOG_FILENAME

    formatter_name = "standard_formatter"
    stdout_handler_name = "stdout_handler"
    rotating_handler_name = "rotating_file_handler"
    logger_name = env.LOGGER__NAME

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            formatter_name: {
                "format": "%(asctime)s [%(threadName)s] [%(levelname)s]: %(message)s"
            }
        },
        "handlers": {
            stdout_handler_name: {
                "class": "logging.StreamHandler",
                "level": env.LOGGER__LOG_LEVEL,
                "formatter": formatter_name,
                "stream": "ext://sys.stdout"
            },
            rotating_handler_name: {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "level": env.LOGGER__LOG_LEVEL,
                "formatter": formatter_name,
                "filename": str(log_file),
                "when": "midnight",
                "backupCount": 0,  # adjust if you want to keep backups
                "encoding": "utf8"
                # suffix and extMatch are not configurable in dictConfig
            }
        },
        "loggers": {
            logger_name: {
                "level": env.LOGGER__LOG_LEVEL,
                "handlers": [stdout_handler_name, rotating_handler_name],
                "propagate": False
            }
        }
    }

    return config

logging.config.dictConfig(setup_logging_config(str(Path(__file__).parent.resolve())))
#logger = setup_logging(str(Path(__file__).parent.resolve()))
logger = logging.getLogger(env.LOGGER__NAME)

server = SanicServer(logger=logger)
app = server.get_app()

if __name__ == "__main__":
    server.run()
