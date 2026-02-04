# 🚀 Быстрые команды для запуска

## Правильные команды:

### Сборка и запуск:
```bash
# Вариант 1: Сначала собрать, потом запустить
docker-compose build
docker-compose up -d

# Вариант 2: Собрать и запустить одной командой
docker-compose up -d --build
```

### Только запуск (если уже собрано):
```bash
docker-compose up -d
```

### Остановка:
```bash
docker-compose down
```

### Перезапуск:
```bash
docker-compose restart
```

### Логи:
```bash
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Статус:
```bash
docker-compose ps
```

## ⚠️ Частые ошибки:

❌ **Неправильно:**
```bash
docker compose docker-compose.yml up -d build
```

✅ **Правильно:**
```bash
docker-compose up -d --build
```

## 📋 Полная последовательность:

```bash
cd ~/ct/pixel_battle

# 1. Создайте .env (если еще не создан)
cat > .env <<EOF
DATABASE_URL=postgresql+asyncpg://pixel_battle_user:pixel_battle_pass@host.docker.internal:6432/pixel_battle_db
REDIS_URL=redis://redis:6379/0
ALLOWED_ORIGINS=http://YOUR_SERVER_IP:8080,http://YOUR_SERVER_IP:8001
VITE_API_URL=http://YOUR_SERVER_IP:8001
VITE_WS_URL=ws://YOUR_SERVER_IP:8001
EOF

# 2. Примените миграции
docker-compose build backend
docker-compose run --rm backend alembic upgrade head

# 3. Запустите всё
docker-compose up -d --build

# 4. Проверьте
docker-compose ps
curl http://localhost:8001/health
```
