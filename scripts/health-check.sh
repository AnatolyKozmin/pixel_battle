#!/bin/bash

# Скрипт для проверки здоровья всех сервисов

set -e

ENV=${1:-prod}
COMPOSE_FILE="docker-compose.yml"

if [ "$ENV" = "prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
fi

echo "Проверка здоровья сервисов в окружении: $ENV"

# Проверка backend
echo "Проверка backend..."
BACKEND_URL=${BACKEND_URL:-http://localhost:8000}
if curl -f -s "$BACKEND_URL/health" > /dev/null; then
    echo "✓ Backend здоров"
else
    echo "✗ Backend недоступен"
    exit 1
fi

# Проверка Redis
echo "Проверка Redis..."
if docker-compose -f $COMPOSE_FILE exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis здоров"
else
    echo "✗ Redis недоступен"
    exit 1
fi

# Проверка PostgreSQL (если используется)
if docker-compose -f $COMPOSE_FILE ps postgres > /dev/null 2>&1; then
    echo "Проверка PostgreSQL..."
    if docker-compose -f $COMPOSE_FILE exec -T postgres pg_isready -U pixel_user > /dev/null 2>&1; then
        echo "✓ PostgreSQL здоров"
    else
        echo "✗ PostgreSQL недоступен"
        exit 1
    fi
fi

# Проверка количества инстансов backend
BACKEND_COUNT=$(docker-compose -f $COMPOSE_FILE ps backend | grep -c "Up" || echo "0")
echo "Количество активных backend инстансов: $BACKEND_COUNT"

echo "Все сервисы здоровы!"
