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


    def _get_headers(self) -> Dict[str, str]:
        """Returns headers with Token, if present."""
        if not self.token:
            logger.error("Attempting request without Token!")
            raise PermissionError("Unauthorized: Token is missing. Login first.")
        return {"Authorization": f"Token {self.token}"}


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
            if isinstance(data, list) and data:
                return data[0]
            if isinstance(data, dict) and 'results' in data:
                return data['results'][0]
            return data


    async def update_profile(self, language: str = None, timezone: str = None) -> Dict:
        """Update user profile settings."""
        profile = await self.get_profile()
        user_id = profile.get('id')
        
        if not user_id:
            raise ValueError("Could not fetch profile id")

        url = f"{self.base_url}/users/profile/{user_id}/"
        
        payload = {}
        if language: payload['language'] = language
        if timezone: payload['timezone'] = timezone
        
        async with self.session.patch(url, json=payload, headers=self._get_headers()) as resp:
            resp.raise_for_status()
            return await resp.json()


    # Tasks
    async def get_tasks(self) -> List[Dict]:
        """Fetch tasks for the authenticated user."""
        if not self.token:
            raise PermissionError("Client is not authenticated.")

        url = f"{self.base_url}/tasks/"
        
        async with self.session.get(url, headers=self._get_headers()) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def create_task(self, title: str, deadline: Optional[str] = None, category_id: Optional[str] = None) -> Dict:
        """Create a new task with optional deadline."""
        if not self.token:
            raise PermissionError("Client is not authenticated.")

        url = f"{self.base_url}/tasks/"
        
        payload = {"title": title}
        if deadline:
            payload["deadline"] = deadline
        if category_id:
            payload["category_id"] = category_id

        async with self.session.post(url, headers=self._get_headers(), json=payload) as resp:
            resp.raise_for_status()
            return await resp.json()
        
        
    async def delete_task(self, task_id: str):
        """Delete task"""
        async with self.session.delete(
                f"{self.base_url}/tasks/{task_id}/",
                headers=self._get_headers(),
            ) as resp:
                resp.raise_for_status()


    async def update_task(self, task_id: str, data: dict):
        """Update task"""
        async with self.session.patch(
                f"{self.base_url}/tasks/{task_id}/", 
                json=data,
                headers=self._get_headers()
            ) as resp:
                resp.raise_for_status()
                return await resp.json()


    async def get_task(self, task_id: str):
        """Get one task (for details window)"""
        async with self.session.get(f"{self.base_url}/tasks/{task_id}/", headers=self._get_headers()) as resp:
            resp.raise_for_status()
            return await resp.json()
        
        
    # Categories
    async def get_categories(self) -> List[Dict]:
        """Fetch categories."""
        if not self.token:
            raise PermissionError("Client is not authenticated.")
            
        url = f"{self.base_url}/categories/"
        
        try:
            async with self.session.get(url, headers=self._get_headers()) as resp:
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
        payload = {"name": name} 
        
        async with self.session.post(url, headers=self._get_headers(), json=payload) as resp:
            resp.raise_for_status()
            return await resp.json()
    
    
    async def delete_category(self, cat_id: str):
        """Delete category"""
        async with self.session.delete(
                f"{self.base_url}/categories/{cat_id}/", 
                headers=self._get_headers()
            ) as resp:
                resp.raise_for_status()
            
            
    async def update_category(self, cat_id: str, name: str):
        """Update category"""
        url = f"{self.base_url}/categories/{cat_id}/"
        payload = {"name": name}
        try:
            async with self.session.patch(
                url, 
                json=payload, 
                headers=self._get_headers()
            ) as resp:
                if resp.status == 400:
                    error_text = await resp.text()
                    logger.error(f"❌ 400 BAD REQUEST на {url}: {error_text}")
                
                resp.raise_for_status()
                return await resp.json()
                
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
                
                
    async def get_category(self, cat_id: str):
        """Get one category details"""
        url = f"{self.base_url}/categories/{cat_id}/"
        try:
            async with self.session.get(
                url, 
                headers=self._get_headers()
            ) as resp:
                if resp.status == 400:
                    error_text = await resp.text()
                    logger.error(f"❌ 400 BAD REQUEST на {url}: {error_text}")
                
                resp.raise_for_status()
                return await resp.json()
                
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise