# Отладка Telegram бота

## Просмотр логов с ошибками

### 1. Все логи с ошибками (рекомендуется)

```bash
docker compose logs backend | grep -i "error\|exception\|traceback\|failed\|bot\|telegram"
```

### 2. Только последние ошибки

```bash
docker compose logs --tail=200 backend | grep -i "error\|exception\|traceback\|failed"
```

### 3. Логи в реальном времени с фильтром

```bash
docker compose logs -f backend | grep -i "error\|exception\|traceback\|failed\|bot\|telegram"
```

### 4. Все логи бота (включая успешные)

```bash
docker compose logs backend | grep -i "bot\|telegram"
```

### 5. Последние 100 строк логов

```bash
docker compose logs --tail=100 backend
```

## Проверка статуса контейнера

```bash
# Проверить, запущен ли контейнер
docker compose ps backend

# Должен показать статус "Up"
```

## Проверка переменных окружения

```bash
# Проверить, установлен ли токен
docker compose exec backend env | grep TELEGRAM_BOT_TOKEN

# Должен показать токен (не пусто)
```

## Проверка подключения к БД

```bash
# Проверить логи на ошибки БД
docker compose logs backend | grep -i "database\|sql\|connection\|asyncpg"
```

## Типичные ошибки и решения

### Ошибка: "TELEGRAM_BOT_TOKEN не установлен"
**Решение:** Добавь токен в `.env` и перезапусти:
```bash
nano .env  # Добавь TELEGRAM_BOT_TOKEN=...
docker compose restart backend
```

### Ошибка: "Invalid token"
**Решение:** Проверь токен в BotFather, возможно он неверный

### Ошибка: "Connection refused" или "Network error"
**Решение:** Проверь интернет-соединение контейнера:
```bash
docker compose exec backend ping -c 3 api.telegram.org
```

### Ошибка: "Database connection failed"
**Решение:** Проверь подключение к БД:
```bash
docker compose logs backend | grep -i "database\|connection"
```

## Полная диагностика одной командой

```bash
echo "=== Статус контейнера ===" && \
docker compose ps backend && \
echo -e "\n=== Токен бота ===" && \
docker compose exec backend env | grep TELEGRAM_BOT_TOKEN && \
echo -e "\n=== Последние ошибки ===" && \
docker compose logs --tail=50 backend | grep -i "error\|exception\|traceback\|failed" && \
echo -e "\n=== Логи бота ===" && \
docker compose logs --tail=30 backend | grep -i "bot\|telegram"
```

## Вход в контейнер для ручной проверки

```bash
# Войти в контейнер
docker compose exec backend bash

# Проверить переменные окружения
env | grep TELEGRAM

# Проверить Python
python -c "from app.core.config import settings; print('Token:', settings.TELEGRAM_BOT_TOKEN[:10] + '...' if settings.TELEGRAM_BOT_TOKEN else 'NOT SET')"

# Выйти
exit
```
