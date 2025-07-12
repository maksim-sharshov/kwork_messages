import logging
import sys
import json
from logging import Logger, getLogger, Formatter, StreamHandler, INFO, ERROR
from logging.handlers import RotatingFileHandler


class JsonFormatter(logging.Formatter):
    """Форматтер, который выводит логи в JSON."""
    def format(self, record):
        log_record = {
            "level": record.levelname,
            "time": self.formatTime(record, self.datefmt),
            "name": record.name,
            "line": record.lineno,
            "filename": record.filename,
            "message": record.getMessage()
        }
        return json.dumps(log_record, ensure_ascii=False)


def setting_logger(
    logger: Logger,
    logs_path: str,
    level=INFO,
    formatter: logging.Formatter | None = None,
    max_bytes=1024 * 1024 * 5,
    backup_count=3,
    stream=sys.stdout,
) -> Logger:
    """
    Настройка логгера с файловым и стрим-хендлерами.
    """
    if formatter is None:
        formatter = Formatter(
            datefmt='%Y-%m-%d %H:%M:%S',
            fmt="%(levelname)s - %(asctime)s - %(name)s - (Line: %(lineno)d) - [%(filename)s]: %(message)s"
        )

    file_handler = RotatingFileHandler(
        filename=logs_path,
        encoding='utf8',
        maxBytes=max_bytes,
        backupCount=backup_count,
    )
    file_handler.setFormatter(formatter)

    stream_handler = StreamHandler(stream=stream)
    stream_handler.setFormatter(formatter)

    logger.handlers = [file_handler, stream_handler]
    logger.setLevel(level)
    logger.propagate = False  # чтобы не дублировались сообщения

    return logger


# Основной логгер
logger = setting_logger(
    logger=getLogger('main_logger'),
    logs_path='logs/logs.log',
)

# Логгер для менеджера
manager_logger = setting_logger(
    logger=getLogger('manager_logger'),
    logs_path='logs/manager.log',
)

# Логгер для диалогов в JSON
dialogs_logger = setting_logger(
    logger=getLogger('dialogs_logger'),
    logs_path='logs/dialogs.json',
    formatter=JsonFormatter(datefmt='%Y-%m-%d %H:%M:%S'),
)

# Логгер для ошибок
error_logger = setting_logger(
    logger=getLogger('error_logger'),
    logs_path='logs/error.log',
    level=ERROR,
)