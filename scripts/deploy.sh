#!/bin/bash

# Скрипт для деплоя приложения

set -e

ENV=${1:-prod}
COMPOSE_FILE="docker-compose.yml"

if [ "$ENV" = "prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
fi

echo "Деплой в окружение: $ENV"
echo "Используется файл: $COMPOSE_FILE"

# Проверка наличия .env файла
if [ ! -f ".env" ]; then
    echo "Ошибка: файл .env не найден!"
    exit 1
fi

# Остановка старых контейнеров
echo "Остановка старых контейнеров..."
docker-compose -f $COMPOSE_FILE down

# Сборка образов
echo "Сборка образов..."
docker-compose -f $COMPOSE_FILE build --no-cache

# Запуск сервисов
echo "Запуск сервисов..."
docker-compose -f $COMPOSE_FILE up -d

# Ожидание готовности
echo "Ожидание готовности сервисов..."
sleep 10

# Проверка статуса
echo "Статус сервисов:"
docker-compose -f $COMPOSE_FILE ps

# Запуск миграций (только для backend)
echo "Запуск миграций БД..."
docker-compose -f $COMPOSE_FILE exec -T backend alembic upgrade head || echo "Миграции уже применены или БД недоступна"

echo "Деплой завершен!"
