# План запуска Telegram бота на сервере

## Шаг 1: Получить токен бота

1. Открой [@BotFather](https://t.me/BotFather) в Telegram
2. Отправь команду `/newbot` (если бота еще нет) или `/token` (если бот уже создан)
3. Следуй инструкциям и получи токен вида: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

## Шаг 2: Добавить токен в .env на сервере

На сервере отредактируй `.env` файл:

```bash
cd ~/ct/pixel_battle
nano .env
```

Добавь или обнови строки:

```bash
# Обязательно - токен бота
TELEGRAM_BOT_TOKEN=твой_токен_бота_здесь

# Опционально - URL для кнопки "Открыть игру" в боте
# Если не указан, кнопка не будет работать, но бот будет работать
TELEGRAM_WEBHOOK_URL=http://твой-ip:5000  # Или https://твой-домен.com
```

**Важно:** Бот работает через **polling** (не webhook), поэтому:
- ✅ Webhook настраивать НЕ нужно
- ✅ `TELEGRAM_BOT_TOKEN` - единственное обязательное поле для работы бота
- ✅ `TELEGRAM_WEBHOOK_URL` нужен только для кнопки "Открыть игру"

Сохрани файл (Ctrl+O, Enter, Ctrl+X в nano).

## Шаг 3: Применить миграцию базы данных

```bash
cd ~/ct/pixel_battle
docker compose exec backend alembic upgrade head
```

Это создаст таблицы `teams` и `team_members` в базе данных.

**Проверка миграции:**
```bash
# Проверить текущую версию миграции
docker compose exec backend alembic current

# Должно показать: 002_add_teams (head)
```

## Шаг 4: Перезапустить backend

```bash
docker compose restart backend
```

Или пересобрать, если были изменения в коде:

```bash
docker compose up -d --build backend
```

## Шаг 5: Проверить логи

```bash
# Смотреть логи в реальном времени
docker compose logs -f backend

# Или последние 100 строк
docker compose logs --tail=100 backend
```

**Что искать в логах:**
- ✅ `Telegram бот запущен` - бот успешно стартовал
- ❌ Ошибки с `TELEGRAM_BOT_TOKEN` - токен не установлен или неверный
- ❌ Ошибки подключения к БД - проблемы с миграцией

## Шаг 6: Протестировать бота

1. Найди своего бота в Telegram (по имени, которое ты дал через BotFather)
2. Отправь команду `/start`
3. Бот должен ответить и зарегистрировать тебя

**Тестовые команды:**
```
/start          - Регистрация
/help           - Справка
/create_team Тестовая команда  - Создать команду
/my_teams       - Показать команды
```

## Troubleshooting

### Бот не отвечает

1. **Проверь токен:**
   ```bash
   docker compose exec backend env | grep TELEGRAM_BOT_TOKEN
   ```
   Должен показать токен (не пусто).

2. **Проверь логи на ошибки:**
   ```bash
   docker compose logs backend | grep -i "bot\|telegram\|error"
   ```

3. **Проверь, что бот запущен:**
   ```bash
   docker compose ps backend
   ```
   Статус должен быть `Up`.

### Ошибка миграции

Если миграция не применяется:

```bash
# Проверить текущую версию
docker compose exec backend alembic current

# Применить миграцию вручную
docker compose exec backend alembic upgrade head

# Если есть конфликты, посмотреть историю
docker compose exec backend alembic history
```

### Бот отвечает, но команды не работают

1. Проверь, что пользователь зарегистрирован через `/start`
2. Проверь логи на ошибки БД:
   ```bash
   docker compose logs backend | grep -i "database\|sql\|error"
   ```

### Перезапуск бота

Если нужно перезапустить только бота (без всего backend):

```bash
# Остановить бот (остановит весь backend)
docker compose stop backend

# Запустить снова
docker compose start backend
```

## Проверка работы команды

После создания команды через `/create_team`, проверь в БД:

```bash
# Подключиться к БД (если есть доступ)
docker compose exec backend python -c "
from app.core.database import AsyncSessionLocal
from app.models.team import Team
import asyncio

async def check():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(Team))
        teams = result.scalars().all()
        for team in teams:
            print(f'Team: {team.name}, Code: {team.code}, Owner: {team.owner_id}')

asyncio.run(check())
"
```

## Быстрая проверка всех шагов

```bash
# 1. Проверить токен
docker compose exec backend env | grep TELEGRAM_BOT_TOKEN

# 2. Проверить миграцию
docker compose exec backend alembic current

# 3. Проверить статус
docker compose ps backend

# 4. Проверить логи
docker compose logs --tail=50 backend | grep -i bot
```

## Дополнительно: Переход на webhook (опционально, для production)

**Сейчас бот работает через polling** - это проще и не требует настройки webhook.

Если в будущем захочешь перейти на webhook (для production с высокой нагрузкой):

1. Настрой webhook URL в BotFather: `/setwebhook https://твой-домен.com/api/telegram/webhook`
2. Обнови код в `app/main.py` - замени `start_polling()` на `set_webhook()`
3. Добавь endpoint для приёма обновлений от Telegram
4. Настрой nginx для проксирования webhook запросов

Но для начала **polling достаточно** и работает отлично!
