import logging
from datetime import timedelta
from zoneinfo import ZoneInfo

import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import Task

logger = logging.getLogger(__name__)


def get_local_time_str(dt, user):
    """
    UTC datetime -> User timezone
    """
    if not dt:
        return ""

    user_tz_name = getattr(user, "timezone", None)

    if user_tz_name:
        try:
            local_dt = dt.astimezone(ZoneInfo(user_tz_name))
            return local_dt.strftime("%H:%M")
        except Exception:
            pass

    return dt.strftime("%H:%M (UTC)")


@shared_task
def check_deadlines():
    """
    Periodic task.
    Searches for tasks whose deadline has passed,
    but the notification has not yet been sent.
    """
    now = timezone.now()

    warning_limit = now + timedelta(minutes=10)

    upcoming_tasks = Task.objects.filter(
        deadline__gt=now,  # Deadline__gt = Greater Than
        deadline__lte=warning_limit,
        is_completed=False,
        is_pre_notified=False,
    ).select_related("user")

    for task in upcoming_tasks:
        user = task.user
        if not user.telegram_id:
            continue

        minutes_left = int((task.deadline - now).total_seconds() / 60)

        message_text = f"⏳ <b>Reminder!</b>\n\nTask: <b>{task.title}</b>\nDue in: <b>{minutes_left} min</b>"

        send_telegram_message(user.telegram_id, message_text)

        task.is_pre_notified = True
        task.save(update_fields=["is_pre_notified"])

    expired_tasks = Task.objects.filter(
        deadline__lte=now,  # deadline__lte = Less Than or Equal
        is_completed=False,
        is_notified=False,
    ).select_related("user")

    for task in expired_tasks:
        user = task.user
        if not user.telegram_id:
            continue

        message_text = (
            f"🔥 <b>DEADLINE REACHED!</b>\n\nTask: <b>{task.title}</b>\nTime: {task.deadline.strftime('%H:%M')}"
        )

        send_telegram_message(user.telegram_id, message_text)

        task.is_notified = True
        task.save()

    return f"Checked deadlines. Notifications sent: {len(expired_tasks)}"


def send_telegram_message(chat_id, text):
    """Raw request to the Telegram API"""
    if not settings.BOT_TOKEN:
        logger.warning("❌ BOT_TOKEN not found in settings")
        return

    url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        logger.error(f"❌ Failed to send notification: {e}")
