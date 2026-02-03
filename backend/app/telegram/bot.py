"""
Telegram Bot для авторизации и уведомлений
"""
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from app.core.config import settings


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "Привет! Добро пожаловать в Pixel Battle!\n\n"
        "Используй кнопку ниже, чтобы открыть игру:",
        reply_markup={
            "inline_keyboard": [[
                {
                    "text": "🎨 Открыть игру",
                    "web_app": {"url": settings.TELEGRAM_WEBHOOK_URL}
                }
            ]]
        }
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stats"""
    # TODO: Получить статистику пользователя из БД
    await update.message.reply_text("Статистика будет здесь")


def setup_bot():
    """Настройка и запуск бота"""
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    
    return application
