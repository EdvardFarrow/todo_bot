import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_dialog import setup_dialogs
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, API_BASE_URL
from client import APIClient
from handlers.start import router as start_router
from dialogs import main_dialog, setup_dialog


logger = logging.getLogger(__name__)

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    
    logger.info("Bot is starting...")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
    dp = Dispatcher(storage=MemoryStorage())

    client = APIClient(base_url=API_BASE_URL)
    await client.create_session()
    logger.info(f"API Client initialized at {API_BASE_URL}")

    dp.workflow_data.update({"api_client": client})

    dp.include_router(start_router)
    
    dp.include_router(main_dialog)
    dp.include_router(setup_dialog)
    
    setup_dialogs(dp)

    logger.info("✅ Bot is ready to poll. Press Ctrl+C to stop.")
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
    finally:
        logger.info("🛑 Shutting down...")
        await client.close()
        await bot.session.close()
        logger.info("Bye!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually")