import logging
from typing import Dict
from aiogram_dialog import DialogManager
from client import APIClient


logger = logging.getLogger(__name__)

async def get_my_tasks(dialog_manager: DialogManager, **kwargs) -> Dict:
    """
    Loads the user's task list.
    Used in the task_list_window
    """
    client: APIClient = dialog_manager.middleware_data.get("api_client")
    user = dialog_manager.event.from_user
    
    try:
        tasks = await client.get_tasks()
        return {
            "tasks": tasks,
            "count": len(tasks),
            "username": user.first_name or user.username
        }
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        return {
            "tasks": [], 
            "count": 0, 
            "username": user.first_name,
            "error": str(e) 
        }

async def get_categories(dialog_manager: DialogManager, **kwargs) -> Dict:
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