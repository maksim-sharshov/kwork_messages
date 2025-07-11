from datetime import datetime

import pytz


def weekend_time() -> bool:
    """
    Выходное ли сейчас время?
    :return: bool
    """
    now = datetime.now(pytz.timezone('Europe/Moscow'))

    return now.weekday() in [5, 6] or now.hour >= 21 or now.hour < 10
    # return now.hour >= 21 or now.hour < 10
