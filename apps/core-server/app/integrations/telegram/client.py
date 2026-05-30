import logging
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self):
        self.settings = get_settings()
        self.bot = Bot(self.settings.telegram_bot_token) if self.settings.telegram_enabled and self.settings.telegram_bot_token else None

    async def send_inventory_summary(self, text: str) -> None:
        if not self.bot or not self.settings.telegram_warehouse_chat_id:
            logger.info("telegram_disabled_or_unconfigured")
            return
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("Generate Excel", callback_data="report:inventory:xlsx"),
            InlineKeyboardButton("Generate PDF", callback_data="report:inventory:pdf"),
        ]])
        await self.bot.send_message(chat_id=self.settings.telegram_warehouse_chat_id, text=text, reply_markup=keyboard)
