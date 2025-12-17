from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from client import APIClient

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, api_client: APIClient):
    """
    Handle /start command.
    Try to login to Django API.
    """
    user = message.from_user
    
    await message.answer("🔄 Connecting to Backend...")
    
    try:
        # Auth logic
        data = await api_client.login(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name
        )
        
        token_snippet = data['token'][:5] + "..."
        backend_user_id = data['user_id']
        
        await message.answer(
            f"✅ **Success!**\n\n"
            f"Django User ID: `{backend_user_id}` (Snowflake)\n"
            f"Token: `{token_snippet}`\n\n"
            f"API connection established."
        )
        
    except Exception as e:
        await message.answer(f"❌ **Error:** Could not connect to Django.\n{e}")