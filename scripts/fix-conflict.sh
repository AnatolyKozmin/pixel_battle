#!/bin/bash

# Скрипт для разрешения git конфликта в docker-compose.ip.yml

set -e

echo "🔧 Разрешение git конфликта..."

# Проверяем, есть ли конфликт
if ! grep -q "<<<<<<< " docker-compose.ip.yml 2>/dev/null; then
    echo "✅ Конфликт уже разрешен или отсутствует"
    exit 0
fi

echo "📝 Находим и разрешаем конфликт..."

# Создаем резервную копию
cp docker-compose.ip.yml docker-compose.ip.yml.conflict-backup

# Убираем маркеры конфликта
# Удаляем блоки между <<<<<<< и >>>>>>>
sed -i.bak '/<<<<<<< /,/>>>>>>> Stashed changes/d' docker-compose.ip.yml
sed -i.bak '/=======/d' docker-compose.ip.yml

# Убираем дублирующиеся строки комментариев
sed -i.bak '/^# Использование: docker-compose -f docker-compose.ip.yml up -d$/N;/^# Использование: docker-compose -f docker-compose.ip.yml up -d\n# Использование: docker-compose -f docker-compose.ip.yml up -d$/d' docker-compose.ip.yml

# Проверяем результат
if grep -q "<<<<<<< " docker-compose.ip.yml 2>/dev/null; then
    echo "❌ Ошибка: конфликт не разрешен полностью"
    echo "Восстанавливаем из резервной копии..."
    cp docker-compose.ip.yml.conflict-backup docker-compose.ip.yml
    exit 1
fi

echo "✅ Конфликт разрешен"

# Добавляем файл в git
git add docker-compose.ip.yml

echo "✅ Файл добавлен в git"
echo ""
echo "📋 Следующие шаги:"
echo "1. Проверьте: git status"
echo "2. Если все ок, можно сделать: git pull"
echo "3. Затем настройте IP: ./scripts/setup-ip.sh YOUR_IP"
