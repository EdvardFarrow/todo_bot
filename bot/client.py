import aiohttp
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class APIClient:
    """
    Async client to interact with Django REST API.
    Handles Authentication, CRUD operations, and User Profile.
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

    async def login(self, telegram_id: int, username: str, first_name: str, language_code: str = "en") -> Dict[str, Any]:
        """
        Authenticates user via Telegram ID and updates/creates user in DB.
        Passes language_code for Zero-Click Onboarding.
        """
        url = f"{self.base_url}/users/auth/telegram/"
        payload = {
            "telegram_id": telegram_id,
            "username": username or f"tg_{telegram_id}",
            "first_name": first_name,
            "language_code": language_code 
        }
        
        if not self.session:
            await self.create_session()

        try:
            async with self.session.post(url, json=payload) as resp:
                resp.raise_for_status()
                data = await resp.json()
                self.token = data["token"]
                return data
        except aiohttp.ClientError as e:
            logger.error(f"Auth failed: {e}")
            raise

    async def get_profile(self) -> Dict:
        """Fetch user profile (language, timezone)."""
        if not self.token:
            raise PermissionError("Unauthorized")
        
        url = f"{self.base_url}/users/profile/"
        headers = {"Authorization": f"Token {self.token}"}
        
        async with self.session.get(url, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
            if data:
                return data[0]
            return {}

    async def update_profile(self, language: str = None, timezone: str = None) -> Dict:
        """Update user profile settings."""
        profile = await self.get_profile()
        user_id = profile.get('id')
        if not user_id:
            raise ValueError("Could not fetch profile id")

        url = f"{self.base_url}/users/profile/{user_id}/"
        headers = {"Authorization": f"Token {self.token}"}
        
        payload = {}
        if language: payload['language'] = language
        if timezone: payload['timezone'] = timezone
        
        async with self.session.patch(url, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_tasks(self) -> List[Dict]:
        """Fetch tasks for the authenticated user."""
        if not self.token:
            raise PermissionError("Client is not authenticated.")

        url = f"{self.base_url}/tasks/"
        headers = {"Authorization": f"Token {self.token}"}
        
        async with self.session.get(url, headers=headers) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def create_task(self, title: str, deadline: Optional[str] = None, category_id: Optional[str] = None) -> Dict:
        """Create a new task with optional deadline."""
        if not self.token:
            raise PermissionError("Client is not authenticated.")

        url = f"{self.base_url}/tasks/"
        headers = {"Authorization": f"Token {self.token}"}
        
        payload = {"title": title}
        if deadline:
            payload["deadline"] = deadline
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
        try:
            async with self.session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                return []
        except Exception as e:
            logging.error(f"Error getting categories: {e}")
            return []
        
    
    async def create_category(self, name: str) -> dict:
        """Create category"""
        if not self.token:
            raise PermissionError("No token")
            
        url = f"{self.base_url}/categories/"
        headers = {"Authorization": f"Token {self.token}"}
        payload = {"name": name} 
        
        async with self.session.post(url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            return await resp.json()
    
    