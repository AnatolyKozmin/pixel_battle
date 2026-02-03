# Быстрый старт

## Docker Compose (рекомендуется)

### 1. Настройка окружения

```bash
# Скопируйте пример конфигурации
cp backend/.env.example backend/.env

# Отредактируйте .env файл
nano backend/.env
```

Минимальные настройки:
- `DATABASE_URL` - подключение к PostgreSQL
- `REDIS_URL` - подключение к Redis (или используйте встроенный)
- `TELEGRAM_BOT_TOKEN` - токен бота от @BotFather
- `APP_SECRET_KEY` - любой секретный ключ

### 2. Запуск

```bash
# Запуск всех сервисов
docker-compose up -d

# Запуск миграций
docker-compose exec backend alembic upgrade head

# Проверка статуса
docker-compose ps
```

### 3. Проверка работы

```bash
# Health check
curl http://localhost:8000/health

# Логи
docker-compose logs -f backend
```

## Масштабирование

### Docker Compose

```bash
# Увеличить количество backend инстансов до 3
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Или через Makefile
make scale-backend REPLICAS=3
```

### Docker Swarm

```bash
# Инициализация swarm
docker swarm init

# Деплой стека
docker stack deploy -c docker-compose.swarm.yml pixel_battle

# Масштабирование
docker service scale pixel_battle_backend=5

# Просмотр статуса
docker service ls
docker service ps pixel_battle_backend
```

### Kubernetes

```bash
# Создание секретов
kubectl create secret generic pixel-battle-secrets \
  --from-literal=database-url="postgresql+asyncpg://..." \
  --from-literal=telegram-bot-token="..." \
  --from-literal=app-secret-key="..."

# Применение манифестов
kubectl apply -f k8s/

# Масштабирование
kubectl scale deployment pixel-battle-backend --replicas=5

# Просмотр статуса
kubectl get pods -l app=pixel-battle-backend
```

## Полезные команды

### Makefile

```bash
# Показать все команды
make help

# Запуск
make up

# Логи
make logs

# Масштабирование
make scale-backend REPLICAS=5

# Health check
make health

# Деплой
make deploy
```

### Docker Compose

```bash
# Остановка
docker-compose down

# Перезапуск
docker-compose restart

# Пересборка
docker-compose build --no-cache

# Логи конкретного сервиса
docker-compose logs -f backend

# Выполнение команды в контейнере
docker-compose exec backend alembic upgrade head
```

## Troubleshooting

### Проблемы с подключением к БД

```bash
# Проверка подключения
docker-compose exec backend python -c "from app.core.database import engine; import asyncio; asyncio.run(engine.connect())"

# Проверка переменных окружения
docker-compose exec backend env | grep DATABASE
```

### Проблемы с Redis

```bash
# Проверка Redis
docker-compose exec redis redis-cli ping

# Проверка pub/sub
docker-compose exec redis redis-cli PUBSUB CHANNELS
```

### Проблемы с масштабированием

```bash
# Проверка всех инстансов
docker-compose ps backend

# Логи всех инстансов
docker-compose logs backend

# Проверка нагрузки
docker stats
```

## Production деплой

1. **Подготовка**:
   ```bash
   # Создайте production .env файл
   cp backend/.env.example backend/.env.prod
   # Настройте все переменные
   ```

2. **Сборка образов**:
   ```bash
   docker-compose -f docker-compose.prod.yml build
   ```

3. **Деплой**:
   ```bash
   ./scripts/deploy.sh prod
   ```

4. **Масштабирование**:
   ```bash
   ./scripts/scale-backend.sh 5
   ```

5. **Мониторинг**:
   ```bash
   ./scripts/health-check.sh prod
   ```

## Следующие шаги

- Настройте SSL сертификаты для HTTPS
- Настройте мониторинг (Prometheus + Grafana)
- Настройте логирование (Sentry, Loguru)
- Настройте бэкапы БД
- Проведите нагрузочное тестирование
