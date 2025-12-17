import requests
from celery import shared_task
from django.utils import timezone
from .models import Task
from decouple import config
import logging


logger = logging.getLogger(__name__)



BOT_TOKEN = config("BOT_TOKEN") 

@shared_task
def check_deadlines():
    """
    Periodic task.
    Searches for tasks whose deadline has passed,
    but the notification has not yet been sent.
    """
    now = timezone.now()
    
    expired_tasks = Task.objects.filter(
        deadline__lte=now,   # deadline__lte = Less Than or Equal
        is_completed=False,
        is_notified=False
    ).select_related('user') 

    for task in expired_tasks:
        user = task.user
        if not user.telegram_id:
            continue
            
        message_text = (
            f"🔥 <b>DEADLINE REACHED!</b>\n\n"
            f"Task: <b>{task.title}</b>\n"
            f"Time: {task.deadline.strftime('%H:%M')}"
        )
        
        send_telegram_message(user.telegram_id, message_text)
        
        task.is_notified = True
        task.save()
        
    return f"Checked deadlines. Notifications sent: {len(expired_tasks)}"

def send_telegram_message(chat_id, text):
    """Raw request to the Telegram API"""
    if not BOT_TOKEN:
        logger.warning("❌ BOT_TOKEN not found in settings")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        logger.error(f"❌ Failed to send notification: {e}")