#!/bin/bash

# Скрипт для настройки запуска по IP адресу

set -e

echo "🚀 Настройка Pixel Battle для запуска по IP"

# Получаем IP адрес сервера
if [ -z "$1" ]; then
    echo "Введите IP адрес сервера:"
    read SERVER_IP
else
    SERVER_IP=$1
fi

if [ -z "$SERVER_IP" ]; then
    echo "❌ IP адрес не указан!"
    exit 1
fi

echo "📝 Используется IP: $SERVER_IP"

# Обновляем backend .env
if [ -f "backend/.env" ]; then
    echo "Обновление backend/.env..."
    sed -i.bak "s|ALLOWED_ORIGINS=.*|ALLOWED_ORIGINS=http://${SERVER_IP}:5173,http://${SERVER_IP}:80,http://localhost:5173|g" backend/.env
    echo "✅ backend/.env обновлен"
else
    echo "⚠️  backend/.env не найден, создайте его вручную"
fi

# Обновляем frontend .env
if [ -f "frontend/.env" ]; then
    echo "Обновление frontend/.env..."
    echo "VITE_API_URL=http://${SERVER_IP}:8000" > frontend/.env
    echo "VITE_WS_URL=ws://${SERVER_IP}:8000" >> frontend/.env
    echo "✅ frontend/.env обновлен"
else
    echo "Создание frontend/.env..."
    echo "VITE_API_URL=http://${SERVER_IP}:8000" > frontend/.env
    echo "VITE_WS_URL=ws://${SERVER_IP}:8000" >> frontend/.env
    echo "✅ frontend/.env создан"
fi

# Обновляем docker-compose.ip.yml
if [ -f "docker-compose.ip.yml" ]; then
    echo "Обновление docker-compose.ip.yml..."
    sed -i.bak "s/YOUR_SERVER_IP/${SERVER_IP}/g" docker-compose.ip.yml
    echo "✅ docker-compose.ip.yml обновлен"
fi

# Проверка firewall
echo ""
echo "🔒 Проверка firewall..."
if command -v ufw &> /dev/null; then
    echo "Открытие портов в firewall..."
    sudo ufw allow 8000/tcp comment "Pixel Battle Backend"
    sudo ufw allow 80/tcp comment "Pixel Battle Frontend"
    sudo ufw allow 5173/tcp comment "Pixel Battle Frontend Dev"
    echo "✅ Порты открыты"
else
    echo "⚠️  ufw не установлен, откройте порты вручную: 8000, 80, 5173"
fi

echo ""
echo "✅ Настройка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Проверьте настройки в backend/.env и frontend/.env"
echo "2. Запустите: docker-compose -f docker-compose.ip.yml up -d"
echo "3. Откройте в браузере: http://${SERVER_IP}:80"
echo ""
echo "⚠️  ВАЖНО: Это только для тестирования! Для production нужен HTTPS."
