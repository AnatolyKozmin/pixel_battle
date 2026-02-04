#!/bin/bash
set -e

# Функция для ожидания готовности PostgreSQL
wait_for_postgres() {
    echo "Ожидание готовности PostgreSQL..."
    until PGPASSWORD="${POSTGRES_PASSWORD:-pixel_pass}" psql -h postgres -U "${POSTGRES_USER:-pixel_user}" -d postgres -c '\q' 2>/dev/null; do
        echo "PostgreSQL недоступен, ожидание..."
        sleep 1
    done
    echo "PostgreSQL готов!"
}

# Функция для создания базы данных, если её нет
create_database_if_not_exists() {
    DB_NAME="${POSTGRES_DB:-pixel_battle}"
    DB_USER="${POSTGRES_USER:-pixel_user}"
    DB_PASSWORD="${POSTGRES_PASSWORD:-pixel_pass}"
    
    echo "Проверка существования базы данных ${DB_NAME}..."
    
    DB_EXISTS=$(PGPASSWORD="${DB_PASSWORD}" psql -h postgres -U "${DB_USER}" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" 2>/dev/null || echo "0")
    
    if [ "$DB_EXISTS" != "1" ]; then
        echo "Создание базы данных ${DB_NAME}..."
        PGPASSWORD="${DB_PASSWORD}" psql -h postgres -U "${DB_USER}" -d postgres -c "CREATE DATABASE ${DB_NAME};" 2>/dev/null || true
        echo "База данных ${DB_NAME} создана или уже существует."
    else
        echo "База данных ${DB_NAME} уже существует."
    fi
}

# Ожидание PostgreSQL
wait_for_postgres

# Создание базы данных, если её нет
create_database_if_not_exists

# Запуск миграций
echo "Запуск миграций Alembic..."
alembic upgrade head

# Запуск приложения
echo "Запуск приложения..."
exec "$@"
