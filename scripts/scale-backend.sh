#!/bin/bash

# Скрипт для масштабирования backend инстансов

set -e

COMPOSE_FILE="docker-compose.prod.yml"
SERVICE_NAME="backend"

# Получаем количество инстансов из аргумента или используем значение по умолчанию
REPLICAS=${1:-2}

echo "Масштабирование сервиса $SERVICE_NAME до $REPLICAS инстансов..."

# Обновляем docker-compose файл с новым количеством реплик
sed -i.bak "s/replicas: [0-9]*/replicas: $REPLICAS/" $COMPOSE_FILE

# Масштабируем сервис
docker-compose -f $COMPOSE_FILE up -d --scale $SERVICE_NAME=$REPLICAS --no-recreate

# Ждем пока все инстансы станут здоровыми
echo "Ожидание готовности инстансов..."
sleep 5

# Проверяем статус
docker-compose -f $COMPOSE_FILE ps $SERVICE_NAME

echo "Масштабирование завершено. Запущено $REPLICAS инстансов."
