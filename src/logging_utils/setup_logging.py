import atexit
import logging
import logging.config
from typing import Any

logging_config = {
    "version": 1,
    "disable_existing_formatters": False,
    "filters": {
        "redacted_filter": {
            "()": "logging_utils.RedactedFilter",
        },
        "joke_filter": {
            "()": "logging_utils.JokeFilter",
        },
    },
    "formatters": {
        "simple": {
            "format": "%(levelname)s: %(message)s"
        },
        "json": {
            "()": "logging_utils.JSONFormatter",
            "fmt_keys": {
                "level": "levelname",
                "message": "message",
                "timestamp": "timestamp",
                "logger": "name",
                "module": "module",
                "function": "funcName",
                "line": "lineno",
                "thread_name": "threadName",
            }
        },
        "color": {
            "()": "logging_utils.ColorFormatter",
            "fmt": "[%(levelname)-8s | %(module)-15s | L%(lineno)-4d] %(asctime)s: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z"
        }
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "color",
            "filters": ["redacted_filter",],
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "json",
            "filters": ["joke_filter"],
            "filename": "logs/log.jsonl",
            "maxBytes": 10_000,
            "backupCount": 3,
        },
        "queue_handler": {
            "class": "logging.handlers.QueueHandler",
            "handlers": [
                "stdout",
                "file"
            ],
            "respect_handler_level": True
        }
    },
    "loggers": {
        "root": {
            "level": "DEBUG",
            "handlers": [
                "queue_handler",
            ]
        }
    }
}

def setup_logging(settings_general):
    if settings_general is not None:
        logging_config["handlers"]["file"]["maxBytes"] = settings_general["logfile_maxsize_mb"] * 1_000_000
        logging_config["handlers"]["stdout"]["level"] = settings_general["loglevel"].upper()
        if settings_general["loglevel"].upper() != "DEBUG":
            logging_config["formatters"]["color"]["fmt"] = "[%(levelname)-8s] %(asctime)s: %(message)s"
    logging.config.dictConfig(logging_config)
    queue_handler = logging.getHandlerByName("queue_handler")
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)
