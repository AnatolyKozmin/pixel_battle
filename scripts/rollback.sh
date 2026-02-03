#!/bin/bash

# Скрипт для отката к предыдущей версии

set -e

ENV=${1:-prod}
COMPOSE_FILE="docker-compose.yml"

if [ "$ENV" = "prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
fi

echo "Откат в окружении: $ENV"

# Остановка текущих контейнеров
echo "Остановка текущих контейнеров..."
docker-compose -f $COMPOSE_FILE down

# Восстановление из бэкапа (если есть)
if [ -f "backup/docker-compose.prod.yml.backup" ]; then
    echo "Восстановление из бэкапа..."
    cp backup/docker-compose.prod.yml.backup $COMPOSE_FILE
fi

# Запуск предыдущей версии
echo "Запуск предыдущей версии..."
docker-compose -f $COMPOSE_FILE up -d

echo "Откат завершен!"
