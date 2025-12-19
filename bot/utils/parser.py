import datetime

import pytz
from dateparser.search import search_dates


def parse_task_text(text: str, user_timezone: str = "UTC") -> tuple[str, datetime.datetime | None]:
    """
    Extracts the task description and deadline date from the text.
    Returns: (clean_title, deadline_datetime)
    """
    settings = {
        "PREFER_DATES_FROM": "future",
        "TIMEZONE": user_timezone,
        "RETURN_AS_TIMEZONE_AWARE": True,
        "SKIP_TOKENS": ["at", "on", "in", "в", "на", "через"],
    }

    # search_dates return a list of tuples: [('in 2 minutes', datetime_obj), ...]
    found_dates = search_dates(text, languages=["en", "ru"], settings=settings)

    if not found_dates:
        return text, None

    date_str, deadline_dt = found_dates[-1]

    # Example: "Buy milk tomorrow" -> "Buy milk"
    clean_title = text.replace(date_str, "").strip()

    for prep in [" in", " at", " on", " в", " на", " через"]:
        if clean_title.endswith(prep):
            clean_title = clean_title[: -len(prep)].strip()

    if not clean_title:
        clean_title = text

    if deadline_dt:
        deadline_dt = deadline_dt.astimezone(pytz.utc)

    return clean_title, deadline_dt
