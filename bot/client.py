import aiohttp
import logging
from typing import Optional, Dict, Any, List


class APIClient:
    """
    Async client to interact with Django REST API.
    Handles Authentication and CRUD operations.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.token: Optional[str] = None

    async def create_session(self) -> None:
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close(self) -> None:
        if self.session:
            await self.session.close()

    async def login(self, telegram_id: int, username: str, first_name: str) -> Dict[str, Any]:
        """
        Authenticates user via Telegram ID.
        Django will find existing user or create a new one.
        Returns: Dict with 'token' and 'user_id'
        """
        url = f"{self.base_url}/users/auth/telegram/"
        payload = {
            "telegram_id": telegram_id,
            "username": username or f"tg_{telegram_id}", # Handle cases with no username
            "first_name": first_name
        }
        
        if not self.session:
            await self.create_session()

        try:
            async with self.session.post(url, json=payload) as resp:
                resp.raise_for_status() # Raise error for 4xx/5xx
                data = await resp.json()
                self.token = data["token"]
                return data
        except aiohttp.ClientError as e:
            logging.error(f"Auth failed: {e}")
            raise

    async def get_tasks(self) -> List[Dict]:
        """Fetch tasks for the authenticated user."""
        if not self.token:
            raise PermissionError("Client is not authenticated.")

        url = f"{self.base_url}/tasks/"
        headers = {"Authorization": f"Token {self.token}"}
        
        async with self.session.get(url, headers=headers) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def create_task(self, title: str, category_id: Optional[str] = None) -> Dict:
        """Create a new task."""
        if not self.token:
            raise PermissionError("Client is not authenticated.")

        url = f"{self.base_url}/tasks/"
        headers = {"Authorization": f"Token {self.token}"}
        payload = {"title": title}
        if category_id:
            payload["category_id"] = category_id

        async with self.session.post(url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            return await resp.json()
            
    async def get_categories(self) -> List[Dict]:
        """Fetch categories."""
        if not self.token:
            raise PermissionError("Client is not authenticated.")
            
        url = f"{self.base_url}/categories/"
        headers = {"Authorization": f"Token {self.token}"}
        async with self.session.get(url, headers=headers) as resp:
            resp.raise_for_status()
            return await resp.json()