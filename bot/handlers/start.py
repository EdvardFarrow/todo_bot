import html

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from bot.client import APIClient
from bot.states.state import MainSG, SetupSG

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, dialog_manager: DialogManager, api_client: APIClient):
    """
    Entry point. Authenticates user and decides routing
    """
    user = message.from_user

    try:
        await api_client.login(
            telegram_id=user.id, username=user.username, first_name=user.first_name, language_code=user.language_code
        )

        profile = await api_client.get_profile()
        timezone = profile.get("timezone", "UTC")

        if timezone == "UTC":
            await dialog_manager.start(state=SetupSG.timezone, mode=StartMode.RESET_STACK)
        else:
            await dialog_manager.start(state=MainSG.menu, mode=StartMode.RESET_STACK)

    except Exception as e:
        await message.answer(f"❌ <b>Connection Error:</b>\n<code>{html.escape(str(e))}</code>")
