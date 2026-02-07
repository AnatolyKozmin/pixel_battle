"""
Telegram Bot для авторизации, уведомлений и работы с командами
"""
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.services.user_service import UserService
from app.schemas.user import UserCreate
from app.services.team_service import TeamService


async def get_db():
    """Получить сессию БД для бота"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start - регистрация пользователя"""
    user = update.effective_user
    if not user:
        await update.message.reply_text("Ошибка: не удалось получить информацию о пользователе")
        return
    
    async for db in get_db():
        # Создаем или получаем пользователя
        user_data = UserCreate(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        db_user = await UserService.get_or_create_user(db, user_data)
        
        await update.message.reply_text(
            f"Привет, {user.first_name or user.username or 'друг'}! 👋\n\n"
            f"Ты зарегистрирован в Pixel Battle!\n\n"
            f"📋 Доступные команды:\n"
            f"/my_teams - Мои команды\n"
            f"/create_team <название> - Создать команду\n"
            f"/join_team <код> - Присоединиться к команде\n"
            f"/help - Справка по командам\n\n"
            f"Используй кнопку ниже, чтобы открыть игру:",
            reply_markup={
                "inline_keyboard": [[
                    {
                        "text": "🎨 Открыть игру",
                        "web_app": {"url": settings.TELEGRAM_WEBHOOK_URL}
                    }
                ]]
            }
        )
        break


async def create_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создать новую команду"""
    user = update.effective_user
    if not user:
        await update.message.reply_text("Ошибка: не удалось получить информацию о пользователе")
        return
    
    # Получаем название команды из аргументов
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "❌ Укажи название команды!\n\n"
            "Пример: /create_team Моя команда"
        )
        return
    
    team_name = " ".join(context.args)
    if len(team_name) > 255:
        await update.message.reply_text("❌ Название команды слишком длинное (максимум 255 символов)")
        return
    
    async for db in get_db():
        # Получаем пользователя
        db_user = await UserService.get_user_by_telegram_id(db, user.id)
        if not db_user:
            await update.message.reply_text("❌ Пользователь не найден. Используй /start для регистрации")
            return
        
        try:
            team = await TeamService.create_team(db, team_name, db_user.id)
            await update.message.reply_text(
                f"✅ Команда '{team.name}' создана!\n\n"
                f"🔑 Код команды: <code>{team.code}</code>\n\n"
                f"Поделись этим кодом с участниками, чтобы они могли присоединиться:\n"
                f"/join_team {team.code}",
                parse_mode="HTML"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при создании команды: {str(e)}")
        break


async def join_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Присоединиться к команде"""
    user = update.effective_user
    if not user:
        await update.message.reply_text("Ошибка: не удалось получить информацию о пользователе")
        return
    
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "❌ Укажи код команды!\n\n"
            "Пример: /join_team ABC123"
        )
        return
    
    team_code = context.args[0].upper().strip()
    
    async for db in get_db():
        # Получаем пользователя
        db_user = await UserService.get_user_by_telegram_id(db, user.id)
        if not db_user:
            await update.message.reply_text("❌ Пользователь не найден. Используй /start для регистрации")
            return
        
        # Получаем команду
        team = await TeamService.get_team_by_code(db, team_code)
        if not team:
            await update.message.reply_text(f"❌ Команда с кодом '{team_code}' не найдена")
            return
        
        # Проверяем, не состоит ли уже
        if await TeamService.is_user_in_team(db, db_user.id, team.id):
            await update.message.reply_text(f"✅ Ты уже состоишь в команде '{team.name}'")
            return
        
        # Добавляем в команду
        success = await TeamService.add_user_to_team(db, db_user.id, team.id)
        if success:
            await update.message.reply_text(
                f"✅ Ты присоединился к команде '{team.name}'!\n\n"
                f"Код команды: <code>{team.code}</code>",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text("❌ Не удалось присоединиться к команде")
        break


async def my_teams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать мои команды"""
    user = update.effective_user
    if not user:
        await update.message.reply_text("Ошибка: не удалось получить информацию о пользователе")
        return
    
    async for db in get_db():
        # Получаем пользователя
        db_user = await UserService.get_user_by_telegram_id(db, user.id)
        if not db_user:
            await update.message.reply_text("❌ Пользователь не найден. Используй /start для регистрации")
            return
        
        teams = await TeamService.get_user_teams(db, db_user.id)
        
        if not teams:
            await update.message.reply_text(
                "📭 У тебя пока нет команд.\n\n"
                "Создай команду: /create_team <название>\n"
                "Или присоединись: /join_team <код>"
            )
            return
        
        message = "📋 Твои команды:\n\n"
        for team in teams:
            is_owner = await TeamService.is_owner(db, db_user.id, team.id)
            owner_mark = "👑" if is_owner else "👤"
            members_count = len(await TeamService.get_team_members(db, team.id))
            message += f"{owner_mark} <b>{team.name}</b>\n"
            message += f"   Код: <code>{team.code}</code>\n"
            message += f"   Участников: {members_count}\n\n"
        
        await update.message.reply_text(message, parse_mode="HTML")
        break


async def team_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация о команде"""
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "❌ Укажи код команды!\n\n"
            "Пример: /team_info ABC123"
        )
        return
    
    team_code = context.args[0].upper().strip()
    
    async for db in get_db():
        team = await TeamService.get_team_by_code(db, team_code)
        if not team:
            await update.message.reply_text(f"❌ Команда с кодом '{team_code}' не найдена")
            return
        
        members = await TeamService.get_team_members(db, team.id)
        owner = await UserService.get_user_by_id(db, team.owner_id)
        
        message = f"📊 Информация о команде:\n\n"
        message += f"<b>{team.name}</b>\n"
        message += f"Код: <code>{team.code}</code>\n"
        if team.description:
            message += f"Описание: {team.description}\n"
        message += f"Владелец: {owner.first_name or owner.username or 'Неизвестно'}\n"
        message += f"Участников: {len(members)}\n"
        message += f"Создана: {team.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        
        await update.message.reply_text(message, parse_mode="HTML")
        break


async def team_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список участников команды"""
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "❌ Укажи код команды!\n\n"
            "Пример: /team_members ABC123"
        )
        return
    
    team_code = context.args[0].upper().strip()
    
    async for db in get_db():
        team = await TeamService.get_team_by_code(db, team_code)
        if not team:
            await update.message.reply_text(f"❌ Команда с кодом '{team_code}' не найдена")
            return
        
        members = await TeamService.get_team_members(db, team.id)
        owner = await UserService.get_user_by_id(db, team.owner_id)
        
        message = f"👥 Участники команды '{team.name}':\n\n"
        
        # Владелец
        message += f"👑 {owner.first_name or owner.username or 'Неизвестно'}"
        if owner.username:
            message += f" (@{owner.username})"
        message += " - Владелец\n"
        
        # Остальные участники
        for member in members:
            if member.id != owner.id:
                message += f"👤 {member.first_name or member.username or 'Неизвестно'}"
                if member.username:
                    message += f" (@{member.username})"
                message += "\n"
        
        if len(members) == 1:
            message += "\n(Только владелец)"
        
        await update.message.reply_text(message)
        break


async def leave_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покинуть команду"""
    user = update.effective_user
    if not user:
        await update.message.reply_text("Ошибка: не удалось получить информацию о пользователе")
        return
    
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "❌ Укажи код команды!\n\n"
            "Пример: /leave_team ABC123"
        )
        return
    
    team_code = context.args[0].upper().strip()
    
    async for db in get_db():
        # Получаем пользователя
        db_user = await UserService.get_user_by_telegram_id(db, user.id)
        if not db_user:
            await update.message.reply_text("❌ Пользователь не найден. Используй /start для регистрации")
            return
        
        # Получаем команду
        team = await TeamService.get_team_by_code(db, team_code)
        if not team:
            await update.message.reply_text(f"❌ Команда с кодом '{team_code}' не найдена")
            return
        
        # Проверяем, является ли владельцем
        if await TeamService.is_owner(db, db_user.id, team.id):
            await update.message.reply_text(
                "❌ Владелец не может покинуть команду.\n"
                "Используй /delete_team для удаления команды."
            )
            return
        
        # Удаляем из команды
        success = await TeamService.remove_user_from_team(db, db_user.id, team.id)
        if success:
            await update.message.reply_text(f"✅ Ты покинул команду '{team.name}'")
        else:
            await update.message.reply_text("❌ Не удалось покинуть команду")
        break


async def delete_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить команду (только владелец)"""
    user = update.effective_user
    if not user:
        await update.message.reply_text("Ошибка: не удалось получить информацию о пользователе")
        return
    
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "❌ Укажи код команды!\n\n"
            "Пример: /delete_team ABC123"
        )
        return
    
    team_code = context.args[0].upper().strip()
    
    async for db in get_db():
        # Получаем пользователя
        db_user = await UserService.get_user_by_telegram_id(db, user.id)
        if not db_user:
            await update.message.reply_text("❌ Пользователь не найден. Используй /start для регистрации")
            return
        
        # Получаем команду
        team = await TeamService.get_team_by_code(db, team_code)
        if not team:
            await update.message.reply_text(f"❌ Команда с кодом '{team_code}' не найдена")
            return
        
        # Удаляем команду
        success = await TeamService.delete_team(db, team.id, db_user.id)
        if success:
            await update.message.reply_text(f"✅ Команда '{team.name}' удалена")
        else:
            await update.message.reply_text("❌ Ты не являешься владельцем этой команды")
        break


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Справка по командам"""
    help_text = """
📚 <b>Справка по командам Pixel Battle</b>

<b>Основные команды:</b>
/start - Регистрация в системе

<b>Работа с командами:</b>
/create_team &lt;название&gt; - Создать новую команду
/join_team &lt;код&gt; - Присоединиться к команде по коду
/my_teams - Показать все мои команды
/team_info &lt;код&gt; - Информация о команде
/team_members &lt;код&gt; - Список участников команды
/leave_team &lt;код&gt; - Покинуть команду
/delete_team &lt;код&gt; - Удалить команду (только владелец)

<b>Примеры:</b>
/create_team Моя команда
/join_team ABC123
/my_teams
    """
    await update.message.reply_text(help_text, parse_mode="HTML")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stats"""
    user = update.effective_user
    if not user:
        await update.message.reply_text("Ошибка: не удалось получить информацию о пользователе")
        return
    
    async for db in get_db():
        db_user = await UserService.get_user_by_telegram_id(db, user.id)
        if not db_user:
            await update.message.reply_text("❌ Пользователь не найден. Используй /start для регистрации")
            return
        
        await update.message.reply_text(
            f"📊 <b>Твоя статистика:</b>\n\n"
            f"Пикселей размещено: {db_user.pixels_placed}\n"
            f"Дата регистрации: {db_user.created_at.strftime('%d.%m.%Y %H:%M')}",
            parse_mode="HTML"
        )
        break


def setup_bot():
    """Настройка и запуск бота"""
    if not settings.TELEGRAM_BOT_TOKEN:
        print("⚠️  TELEGRAM_BOT_TOKEN не установлен, бот не будет запущен")
        return None
    
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    # Основные команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats))
    
    # Команды для работы с командами
    application.add_handler(CommandHandler("create_team", create_team))
    application.add_handler(CommandHandler("join_team", join_team))
    application.add_handler(CommandHandler("my_teams", my_teams))
    application.add_handler(CommandHandler("team_info", team_info))
    application.add_handler(CommandHandler("team_members", team_members))
    application.add_handler(CommandHandler("leave_team", leave_team))
    application.add_handler(CommandHandler("delete_team", delete_team))
    
    return application
