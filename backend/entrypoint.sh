#!/bin/bash
set -e

# Запуск миграций
echo "Запуск миграций Alembic..."
alembic upgrade head

# Запуск приложения
echo "Запуск приложения..."
exec "$@"
