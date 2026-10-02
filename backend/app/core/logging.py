from __future__ import annotations

import logging
import logging.config


def setup_logging(level: str = "INFO") -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
                }
            },
            "handlers": {
                "console": {"class": "logging.StreamHandler", "formatter": "default"}
            },
            "loggers": {
                "app": {"level": level, "handlers": ["console"], "propagate": False}
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
