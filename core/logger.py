import logging
import sys
from logging import Logger, getLogger, Formatter, StreamHandler, INFO
from logging.handlers import RotatingFileHandler


def setting_logger(logger: Logger, logs_path: str) -> Logger:
    """
        Setting logger. Add handlers formatter etc.
    :param logger: Logger
    :param logs_path: str path to logs file
    """
    # Create formatter
    formatter = Formatter(
        datefmt='%Y-%m-%d %H:%M:%S',
        fmt="%(levelname)s - %(asctime)s - %(name)s - (Line: %(lineno)d) - [%(filename)s]: %(message)s"
    )

    # Creating file handler
    file_handler = RotatingFileHandler(
        filename=logs_path,
        encoding='utf8',
        maxBytes=1024 * 1024 * 5,
        # mode='w'
    )
    file_handler.setFormatter(formatter)

    # Create stream handler
    stream_handler = StreamHandler(
        stream=sys.stdout
    )
    stream_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.handlers = [
        file_handler,
        stream_handler
    ]

    logger.setLevel(INFO)

    return logger


# logging.basicConfig(level=logging.INFO)

# Create loggers
logger = setting_logger(
    logger=getLogger('logger'),
    logs_path='logs/logs.log',
)
manager_logger = setting_logger(
    logger=getLogger('logger'),
    logs_path='logs/manager.log',
)