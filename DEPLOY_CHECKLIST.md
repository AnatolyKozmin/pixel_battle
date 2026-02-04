# ✅ Чеклист готовности к деплою на сервере

## 🔍 Проверка перед запуском

### 1. Docker образы (проверка скачивания)

**Проблема**: Образы могут не скачиваться из-за:
- Проблем с сетью
- Блокировки Docker Hub
- Неправильных тегов образов

**Решение**:

```bash
# Проверьте доступность образов
docker pull postgres:15-alpine
docker pull redis:7-alpine
docker pull python:3.11-slim
docker pull node:18-alpine
docker pull nginx:alpine

# Если не скачивается, попробуйте:
# 1. Проверить интернет-соединение
# 2. Использовать альтернативные registry (если Docker Hub заблокирован)
# 3. Использовать локальные образы
```

**Альтернативные registry** (если Docker Hub недоступен):

```yaml
# В docker-compose.ip.yml можно указать альтернативный registry:
services:
  postgres:
    image: registry.cn-hangzhou.aliyuncs.com/library/postgres:15-alpine
    # или
    image: quay.io/postgres:15-alpine
```

### 2. Конфигурация для сервера

#### Обязательные переменные окружения:

Создайте `.env` файл в корне проекта:

```bash
# Database (если используете внешний PostgreSQL через pgbouncer)
DATABASE_URL=postgresql+asyncpg://user:pass@pgbouncer:6432/pixel_battle
DATABASE_REPLICA_URL=postgresql+asyncpg://user:pass@pgbouncer:6432/pixel_battle

# Redis
REDIS_URL=redis://redis:6379/0

# Telegram (опционально)
TELEGRAM_BOT_TOKEN=your_token_here

# App
APP_SECRET_KEY=change-me-to-secure-random-string
ALLOWED_ORIGINS=http://YOUR_SERVER_IP:80,http://YOUR_SERVER_IP:8000

# Canvas
CANVAS_WIDTH=1000
CANVAS_HEIGHT=1000
```

#### Для IP деплоя:

```bash
# Используйте скрипт автоматической настройки
./scripts/setup-ip.sh YOUR_SERVER_IP

# Или вручную обновите docker-compose.ip.yml:
# Замените все YOUR_SERVER_IP на реальный IP
```

### 3. Проблемы с Docker

#### Проблема: "Unable to find image"

**Решение**:
```bash
# Принудительно скачать образы
docker-compose -f docker-compose.ip.yml pull

# Или использовать build вместо pull
docker-compose -f docker-compose.ip.yml build --no-cache
```

#### Проблема: "Network not found"

**Решение**:
```bash
# Создать сеть вручную
docker network create pixel_battle_network
```

#### Проблема: "Port already in use"

**Решение**:
```bash
# Проверить занятые порты
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :5432

# Остановить конфликтующие сервисы или изменить порты в docker-compose
```

### 4. Проверка зависимостей

#### Backend зависимости:

```bash
# Проверьте requirements.txt
cat backend/requirements.txt

# Основные зависимости должны быть:
# - fastapi
# - uvicorn
# - sqlalchemy
# - asyncpg
# - redis
# - pydantic
```

#### Frontend зависимости:

```bash
# Проверьте package.json
cat frontend/package.json

# Основные зависимости должны быть:
# - vue
# - axios
# - vite
```

### 5. Проверка файлов

#### Обязательные файлы:

```bash
# Backend
- backend/Dockerfile ✅
- backend/entrypoint.sh ✅
- backend/requirements.txt ✅
- backend/app/main.py ✅

# Frontend
- frontend/Dockerfile ✅
- frontend/package.json ✅
- frontend/nginx.conf ✅

# Docker
- docker-compose.ip.yml ✅
- docker-compose.yml ✅
```

### 6. Настройка для production

#### Если используете внешний PostgreSQL (через pgbouncer):

**Важно**: Обновите `docker-compose.ip.yml`:

```yaml
services:
  backend:
    environment:
      # Используйте внешний PostgreSQL
      DATABASE_URL: postgresql+asyncpg://user:pass@pgbouncer:6432/pixel_battle
      DATABASE_REPLICA_URL: postgresql+asyncpg://user:pass@pgbouncer:6432/pixel_battle
    # Уберите зависимость от postgres, если используете внешний
    # depends_on:
    #   - postgres
```

**И удалите/закомментируйте сервис postgres**:

```yaml
# postgres:
#   image: postgres:15-alpine
#   ...
```

#### Если используете внешний Redis:

```yaml
services:
  backend:
    environment:
      REDIS_URL: redis://your-redis-host:6379/0
    # Уберите зависимость от redis
    # depends_on:
    #   - redis
```

**И удалите/закомментируйте сервис redis**:

```yaml
# redis:
#   image: redis:7-alpine
#   ...
```

### 7. Порты и firewall

```bash
# Откройте необходимые порты
sudo ufw allow 80/tcp    # Frontend
sudo ufw allow 8000/tcp  # Backend API
sudo ufw allow 5432/tcp  # PostgreSQL (если не через pgbouncer)
sudo ufw allow 6379/tcp  # Redis (если не через pgbouncer)

# Проверьте статус
sudo ufw status
```

### 8. Запуск и проверка

```bash
# 1. Сборка образов
docker-compose -f docker-compose.ip.yml build

# 2. Запуск
docker-compose -f docker-compose.ip.yml up -d

# 3. Проверка логов
docker-compose -f docker-compose.ip.yml logs -f

# 4. Проверка статуса
docker-compose -f docker-compose.ip.yml ps

# 5. Health check
curl http://YOUR_SERVER_IP:8000/health
```

### 9. Типичные проблемы и решения

#### Проблема: Backend не запускается

```bash
# Проверьте логи
docker-compose -f docker-compose.ip.yml logs backend

# Частые причины:
# - Неправильный DATABASE_URL
# - Отсутствие миграций
# - Проблемы с зависимостями Python
```

**Решение**:
```bash
# Пересоберите образ
docker-compose -f docker-compose.ip.yml build --no-cache backend

# Проверьте entrypoint.sh
cat backend/entrypoint.sh
```

#### Проблема: Frontend не собирается

```bash
# Проверьте логи сборки
docker-compose -f docker-compose.ip.yml logs frontend

# Частые причины:
# - Проблемы с npm install
# - Отсутствие package-lock.json
# - Проблемы с peer dependencies
```

**Решение**:
```bash
# Используйте --legacy-peer-deps (уже в Dockerfile)
# Или пересоберите
docker-compose -f docker-compose.ip.yml build --no-cache frontend
```

#### Проблема: База данных не создается

```bash
# Проверьте entrypoint.sh
# Он должен автоматически создавать БД и запускать миграции

# Проверьте логи
docker-compose -f docker-compose.ip.yml logs backend | grep -i "database\|migration"
```

#### Проблема: CORS ошибки

```bash
# Проверьте ALLOWED_ORIGINS
# Должен включать ваш IP

# В docker-compose.ip.yml:
ALLOWED_ORIGINS: http://YOUR_SERVER_IP:80,http://YOUR_SERVER_IP:8000
```

### 10. Финальная проверка

```bash
# ✅ Все сервисы запущены
docker-compose -f docker-compose.ip.yml ps

# ✅ Backend отвечает
curl http://YOUR_SERVER_IP:8000/health

# ✅ Frontend доступен
curl http://YOUR_SERVER_IP:80

# ✅ WebSocket работает (проверьте в браузере консоль)
# Должно быть: WebSocket connection established
```

## 🚀 Быстрый старт

```bash
# 1. Настройка IP
./scripts/setup-ip.sh YOUR_SERVER_IP

# 2. Запуск
docker-compose -f docker-compose.ip.yml up -d

# 3. Проверка
curl http://YOUR_SERVER_IP:8000/health
```

## 📝 Чеклист перед деплоем

- [ ] Docker образы скачиваются (`docker pull` работает)
- [ ] `.env` файл создан и заполнен
- [ ] `YOUR_SERVER_IP` заменен на реальный IP в `docker-compose.ip.yml`
- [ ] Порты открыты в firewall
- [ ] Внешние сервисы (PostgreSQL, Redis) настроены (если используются)
- [ ] `entrypoint.sh` имеет права на выполнение (`chmod +x`)
- [ ] `DATABASE_REPLICA_URL` указан (если используется replica)
- [ ] `ALLOWED_ORIGINS` включает ваш IP
- [ ] Backend собирается без ошибок
- [ ] Frontend собирается без ошибок
- [ ] Все сервисы запускаются (`docker-compose ps`)
- [ ] Health check проходит (`/health` endpoint)
- [ ] Frontend доступен в браузере

## 🔧 Если что-то не работает

1. **Проверьте логи**: `docker-compose -f docker-compose.ip.yml logs -f`
2. **Проверьте статус**: `docker-compose -f docker-compose.ip.yml ps`
3. **Пересоберите образы**: `docker-compose -f docker-compose.ip.yml build --no-cache`
4. **Очистите всё и начните заново**:
   ```bash
   docker-compose -f docker-compose.ip.yml down -v
   docker-compose -f docker-compose.ip.yml up -d --build
   ```
