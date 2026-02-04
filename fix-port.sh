#!/bin/bash

# Скрипт для исправления порта и перезапуска

echo "🔧 Исправление порта frontend..."

# Останавливаем контейнеры
docker compose down

# Проверяем занятые порты
echo "Проверка занятых портов:"
netstat -tulpn | grep -E ':8080|:3000|:8001' || echo "Порты свободны"

# Обновляем docker-compose.yml если нужно
if grep -q "8080" docker-compose.yml; then
    echo "Обновление порта на 3000..."
    sed -i 's/8080/3000/g' docker-compose.yml
fi

# Создаем .env с правильным IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}' || echo "YOUR_SERVER_IP")
echo "Используется IP: $SERVER_IP"

cat > .env <<EOF
DATABASE_URL=postgresql+asyncpg://pixel_battle_user:pixel_battle_pass@host.docker.internal:6432/pixel_battle_db
REDIS_URL=redis://redis:6379/0
ALLOWED_ORIGINS=http://${SERVER_IP}:3000,http://${SERVER_IP}:8001
VITE_API_URL=http://${SERVER_IP}:8001
VITE_WS_URL=ws://${SERVER_IP}:8001
EOF

echo "✅ .env обновлен"
echo ""
echo "Запуск:"
echo "docker compose up -d"
