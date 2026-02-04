#!/bin/bash

# Скрипт для быстрого локального запуска

set -e

echo "🚀 Запуск Pixel Battle локально..."

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен!"
    echo "Установите Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ docker-compose не установлен!"
    exit 1
fi

# Создание .env файлов если их нет
if [ ! -f "backend/.env" ]; then
    echo "📝 Создание backend/.env..."
    cat > backend/.env << EOF
DATABASE_URL=postgresql+asyncpg://pixel_user:pixel_pass@postgres:5432/pixel_battle
REDIS_URL=redis://redis:6379/0
TELEGRAM_BOT_TOKEN=local-dev-token
APP_SECRET_KEY=local-dev-secret-key-change-me
CANVAS_WIDTH=1000
CANVAS_HEIGHT=1000
PIXEL_COOLDOWN_SECONDS=5
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:80
EOF
    echo "✅ backend/.env создан"
fi

if [ ! -f "frontend/.env" ]; then
    echo "📝 Создание frontend/.env..."
    echo "VITE_API_URL=http://localhost:8000" > frontend/.env
    echo "VITE_WS_URL=ws://localhost:8000" >> frontend/.env
    echo "✅ frontend/.env создан"
fi

# Запуск через docker-compose
echo ""
echo "🐳 Запуск Docker контейнеров..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d --build
else
    docker compose up -d --build
fi

# Ожидание готовности сервисов
echo ""
echo "⏳ Ожидание готовности сервисов..."
sleep 5

# Запуск миграций
echo ""
echo "📦 Запуск миграций БД..."
if command -v docker-compose &> /dev/null; then
    docker-compose exec -T backend alembic upgrade head || echo "⚠️  Миграции уже применены или БД еще не готова"
else
    docker compose exec -T backend alembic upgrade head || echo "⚠️  Миграции уже применены или БД еще не готова"
fi

echo ""
echo "✅ Готово!"
echo ""
echo "📋 Приложение доступно по адресам:"
echo "   Frontend: http://localhost:80"
echo "   Backend API: http://localhost:8000"
echo "   Health check: http://localhost:8000/health"
echo ""
echo "📊 Полезные команды:"
echo "   Логи: docker-compose logs -f"
echo "   Остановка: docker-compose down"
echo "   Перезапуск: docker-compose restart"
echo ""
echo "⚠️  Примечание: Telegram Mini App не будет работать без HTTPS,"
echo "   но обычный веб-интерфейс работает!"
