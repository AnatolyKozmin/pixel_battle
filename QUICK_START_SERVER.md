# 🚀 Быстрый запуск на сервере (HTTP, PostgreSQL в контейнере)

## Для тестирования с небольшой нагрузкой

### 1. Подготовка (один раз)

```bash
# На сервере
cd pixel_battle

# Настройка IP (замените на ваш IP)
./scripts/setup-ip.sh YOUR_SERVER_IP

# Или вручную обновите docker-compose.ip.yml:
# Замените все YOUR_SERVER_IP на реальный IP
```

### 2. Запуск

```bash
# Сборка и запуск всех сервисов
docker-compose -f docker-compose.ip.yml up -d --build

# Или через Makefile (если есть)
make up-ip
```

### 3. Проверка

```bash
# Проверка статуса
docker-compose -f docker-compose.ip.yml ps

# Проверка логов
docker-compose -f docker-compose.ip.yml logs -f

# Health check
curl http://YOUR_SERVER_IP:8000/health
```

### 4. Откройте в браузере

```
http://YOUR_SERVER_IP:80
```

## 📋 Что запускается

- **PostgreSQL** (в контейнере) - порт 5432
- **Redis** (в контейнере) - порт 6379
- **Backend API** - порт 8000
- **Frontend** - порт 80

## ⚙️ Конфигурация

### PostgreSQL в контейнере

Для тестов используется один PostgreSQL контейнер:
- Master и Replica указывают на один и тот же контейнер
- Это нормально для небольшой нагрузки
- При росте нагрузки можно будет переключиться на внешний PostgreSQL с pgbouncer

### Переменные окружения

Можно создать `.env` файл в корне проекта:

```bash
# Database (для контейнера)
POSTGRES_DB=pixel_battle
POSTGRES_USER=pixel_user
POSTGRES_PASSWORD=pixel_pass

# Backend
ALLOWED_ORIGINS=http://YOUR_SERVER_IP:80,http://YOUR_SERVER_IP:8000
TELEGRAM_BOT_TOKEN=your_token_here  # опционально
APP_SECRET_KEY=change-me-to-secure-random-string

# Frontend (автоматически через setup-ip.sh)
VITE_API_URL=http://YOUR_SERVER_IP:8000
VITE_WS_URL=ws://YOUR_SERVER_IP:8000
```

## 🔧 Полезные команды

```bash
# Остановка
docker-compose -f docker-compose.ip.yml down

# Остановка с удалением volumes (осторожно!)
docker-compose -f docker-compose.ip.yml down -v

# Перезапуск
docker-compose -f docker-compose.ip.yml restart

# Логи конкретного сервиса
docker-compose -f docker-compose.ip.yml logs -f backend
docker-compose -f docker-compose.ip.yml logs -f frontend
docker-compose -f docker-compose.ip.yml logs -f postgres

# Пересборка после изменений
docker-compose -f docker-compose.ip.yml up -d --build

# Выполнение команд в контейнере
docker-compose -f docker-compose.ip.yml exec backend alembic upgrade head
docker-compose -f docker-compose.ip.yml exec backend python -c "from app.core.database import engine; print('OK')"
```

## 🐛 Troubleshooting

### Backend не запускается

```bash
# Проверьте логи
docker-compose -f docker-compose.ip.yml logs backend

# Частые причины:
# 1. База данных не создана - entrypoint.sh должен создать автоматически
# 2. Миграции не выполнены - entrypoint.sh должен выполнить автоматически
# 3. Неправильный DATABASE_URL

# Ручной запуск миграций
docker-compose -f docker-compose.ip.yml exec backend alembic upgrade head
```

### Frontend не открывается

```bash
# Проверьте логи
docker-compose -f docker-compose.ip.yml logs frontend

# Проверьте, что порт 80 открыт
sudo ufw allow 80/tcp

# Проверьте, что frontend собран
docker-compose -f docker-compose.ip.yml ps frontend
```

### CORS ошибки

```bash
# Убедитесь, что ALLOWED_ORIGINS включает ваш IP
# В docker-compose.ip.yml должно быть:
ALLOWED_ORIGINS: http://YOUR_SERVER_IP:80,http://YOUR_SERVER_IP:8000

# Перезапустите backend
docker-compose -f docker-compose.ip.yml restart backend
```

### PostgreSQL не запускается

```bash
# Проверьте логи
docker-compose -f docker-compose.ip.yml logs postgres

# Проверьте, что порт 5432 свободен
sudo netstat -tulpn | grep 5432

# Очистите volume и пересоздайте (осторожно - удалит данные!)
docker-compose -f docker-compose.ip.yml down -v
docker-compose -f docker-compose.ip.yml up -d postgres
```

## 📊 Мониторинг

```bash
# Использование ресурсов
docker stats

# Количество подключений к PostgreSQL
docker-compose -f docker-compose.ip.yml exec postgres psql -U pixel_user -d pixel_battle -c "SELECT count(*) FROM pg_stat_activity;"

# Размер базы данных
docker-compose -f docker-compose.ip.yml exec postgres psql -U pixel_user -d pixel_battle -c "SELECT pg_size_pretty(pg_database_size('pixel_battle'));"
```

## ⚠️ Важно

1. **Это для тестирования** - для production нужен HTTPS
2. **PostgreSQL в контейнере** - данные сохраняются в volume `postgres_data`
3. **Небольшая нагрузка** - для тестов этого достаточно
4. **При росте нагрузки** - переключитесь на внешний PostgreSQL с pgbouncer

## 🔄 Миграция на внешний PostgreSQL (когда понадобится)

Когда нагрузка вырастет:

1. Настройте внешний PostgreSQL с pgbouncer
2. Обновите `DATABASE_URL` и `DATABASE_REPLICA_URL` в `.env`
3. Закомментируйте сервис `postgres` в `docker-compose.ip.yml`
4. Уберите `depends_on: postgres` из backend
5. Перезапустите: `docker-compose -f docker-compose.ip.yml up -d`
