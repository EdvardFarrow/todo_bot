import logging

import pytz
from aiogram_dialog import DialogManager
from dateutil import parser

from bot.client import APIClient

logger = logging.getLogger(__name__)


DEFAULT_TZ = pytz.timezone("UTC")


def format_user_time(iso_date_str: str, user_timezone_str: str) -> str:
    """
    "2025-12-17T05:00:00Z" -> "17.12 19:00"
    """
    if not iso_date_str:
        return ""

    try:
        dt_utc = parser.parse(iso_date_str)

        if dt_utc.tzinfo is None:
            dt_utc = pytz.utc.localize(dt_utc)

        try:
            user_tz = pytz.timezone(user_timezone_str)
        except pytz.UnknownTimeZoneError:
            user_tz = DEFAULT_TZ

        dt_local = dt_utc.astimezone(user_tz)

        return dt_local.strftime("%d.%m %H:%M")

    except Exception as e:
        logger.error(f"Date parsing error: {e}")
        return iso_date_str


async def get_my_tasks(dialog_manager: DialogManager, **kwargs) -> dict:
    """
    Loads the user's task list.
    Used in the task_list_window
    """
    client: APIClient = dialog_manager.middleware_data.get("api_client")
    user = dialog_manager.event.from_user

    user_timezone = "UTC"
    try:
        profile = await client.get_profile()
        user_timezone = profile.get("timezone", "UTC")
    except Exception as e:
        logger.warning(f"Could not fetch profile for timezone: {e}")

    try:
        tasks_raw = await client.get_tasks()

        formatted_tasks = []
        for task in tasks_raw:
            created_at_fmt = format_user_time(task.get("created_at"), user_timezone)

            deadline_fmt = format_user_time(task.get("deadline"), user_timezone)

            cat_data = task.get("category")
            cat_title = cat_data.get("title") if isinstance(cat_data, dict) else ""

            display_title = task["title"]

            if task.get("is_completed"):
                display_title = f"✅ {display_title}"
            elif deadline_fmt:
                display_title = f"⏰ {display_title} [{deadline_fmt}]"

            formatted_tasks.append(
                {
                    "id": str(task["id"]),
                    "title": display_title,
                    "created_at": created_at_fmt,
                    "deadline": deadline_fmt,
                    "category": cat_title,
                    "is_completed": task.get("is_completed"),
                }
            )

        return {"tasks": formatted_tasks, "count": len(formatted_tasks), "username": user.first_name or user.username}
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        return {"tasks": [], "count": 0, "username": user.first_name, "error": str(e)}


async def get_task_data(dialog_manager: DialogManager, **kwargs):
    """
    Load a task data
    """
    client: APIClient = dialog_manager.middleware_data.get("api_client")
    task_id = dialog_manager.dialog_data.get("selected_task_id")

    user_tz = "UTC"
    try:
        profile = await client.get_profile()
        user_tz = profile.get("timezone", "UTC")
    except Exception:
        pass

    try:
        task = await client.get_task(task_id)

        deadline_str = task.get("deadline")
        task["deadline_fmt"] = format_user_time(deadline_str, user_tz) or "No deadline"

        created_str = task.get("created_at")
        task["created_at_fmt"] = format_user_time(created_str, user_tz)

        if not task.get("category_name"):
            task["category_name"] = None

        return {"task": task}
    except Exception as e:
        return {
            "task": {
                "title": "Error loading task",
                "deadline_fmt": "Unknown",
                "created_at_fmt": "Unknown",
                "category_name": None,
                "description": str(e),
            }
        }


async def get_categories(dialog_manager: DialogManager, **kwargs) -> dict:
    """
    Loads categories
    """
    client: APIClient = dialog_manager.middleware_data.get("api_client")
    try:
        categories = await client.get_categories()
        return {"categories": categories}
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return {"categories": []}


async def get_category_data(dialog_manager: DialogManager, **kwargs):
    """Load a category data"""
    client = dialog_manager.middleware_data.get("api_client")
    cat_id = dialog_manager.dialog_data.get("selected_cat_id")

    try:
        category = await client.get_category(cat_id)
        return {"cat_id": category["id"], "cat_name": category["name"]}
    except Exception:
        return {"cat_id": cat_id, "cat_name": "Error loading name"}
