# 🔧 Решение проблем с Docker

## Проблема: Образы не скачиваются

### Симптомы:
```
ERROR: pull access denied for postgres:15-alpine
ERROR: Get https://registry-1.docker.io/v2/: net/http: request canceled
ERROR: failed to fetch
```

### Решения:

#### 1. Проверка интернет-соединения

```bash
# Проверьте доступность Docker Hub
curl -I https://registry-1.docker.io/v2/

# Проверьте DNS
nslookup registry-1.docker.io
```

#### 2. Использование альтернативных registry

Если Docker Hub заблокирован, используйте альтернативные:

**Вариант A: Aliyun (Китай)**
```yaml
# В docker-compose.ip.yml замените:
services:
  postgres:
    image: registry.cn-hangzhou.aliyuncs.com/library/postgres:15-alpine
  redis:
    image: registry.cn-hangzhou.aliyuncs.com/library/redis:7-alpine
```

**Вариант B: Quay.io**
```yaml
services:
  postgres:
    image: quay.io/postgres/postgres:15-alpine
  redis:
    image: quay.io/redis/redis:7-alpine
```

**Вариант C: Локальные образы**
```bash
# Скачайте образы заранее на другой машине
docker save postgres:15-alpine redis:7-alpine > images.tar

# На сервере загрузите
docker load < images.tar
```

#### 3. Настройка Docker daemon для прокси

Если нужен прокси:

```bash
# Создайте /etc/docker/daemon.json
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<EOF
{
  "registry-mirrors": [
    "https://registry.cn-hangzhou.aliyuncs.com"
  ]
}
EOF

# Перезапустите Docker
sudo systemctl restart docker
```

#### 4. Использование build вместо pull

Если образы не скачиваются, соберите их локально:

```bash
# Backend и Frontend уже собираются локально
docker-compose -f docker-compose.ip.yml build

# Для postgres и redis используйте альтернативные registry
```

### Обновленный docker-compose.ip.yml с альтернативными registry

Создайте `docker-compose.ip.yml.backup` и используйте этот вариант:

```yaml
services:
  postgres:
    # Альтернатива 1: Aliyun
    image: registry.cn-hangzhou.aliyuncs.com/library/postgres:15-alpine
    # Альтернатива 2: Обычный (если доступен)
    # image: postgres:15-alpine
    
  redis:
    # Альтернатива 1: Aliyun
    image: registry.cn-hangzhou.aliyuncs.com/library/redis:7-alpine
    # Альтернатива 2: Обычный (если доступен)
    # image: redis:7-alpine
```

## Проблема: "No space left on device"

### Решение:

```bash
# Очистка неиспользуемых образов
docker system prune -a

# Очистка volumes
docker volume prune

# Проверка места
df -h
docker system df
```

## Проблема: "Cannot connect to Docker daemon"

### Решение:

```bash
# Проверьте статус Docker
sudo systemctl status docker

# Запустите Docker
sudo systemctl start docker

# Добавьте пользователя в группу docker (чтобы не использовать sudo)
sudo usermod -aG docker $USER
# Выйдите и войдите заново
```

## Проблема: "Port is already allocated"

### Решение:

```bash
# Найдите процесс, использующий порт
sudo lsof -i :8000
sudo lsof -i :80
sudo lsof -i :5432

# Остановите процесс или измените порты в docker-compose
```

## Проблема: "Network not found"

### Решение:

```bash
# Создайте сеть вручную
docker network create pixel_battle_network

# Или удалите и пересоздайте
docker-compose -f docker-compose.ip.yml down
docker-compose -f docker-compose.ip.yml up -d
```

## Проблема: Backend не запускается

### Проверка:

```bash
# Логи
docker-compose -f docker-compose.ip.yml logs backend

# Частые причины:
# 1. Неправильный DATABASE_URL
# 2. База данных не создана
# 3. Миграции не выполнены
# 4. Отсутствуют зависимости Python
```

### Решение:

```bash
# Пересоберите образ
docker-compose -f docker-compose.ip.yml build --no-cache backend

# Проверьте entrypoint.sh
docker-compose -f docker-compose.ip.yml run --rm backend cat /entrypoint.sh

# Запустите миграции вручную
docker-compose -f docker-compose.ip.yml run --rm backend alembic upgrade head
```

## Проблема: Frontend не собирается

### Проверка:

```bash
# Логи сборки
docker-compose -f docker-compose.ip.yml logs frontend

# Частые причины:
# 1. Проблемы с npm install
# 2. Отсутствие package-lock.json
# 3. Peer dependency conflicts
```

### Решение:

```bash
# Пересоберите с очисткой кеша
docker-compose -f docker-compose.ip.yml build --no-cache frontend

# Проверьте package.json
cat frontend/package.json

# Убедитесь, что используется --legacy-peer-deps (уже в Dockerfile)
```

## Быстрая диагностика

```bash
# 1. Проверка Docker
docker --version
docker-compose --version

# 2. Проверка образов
docker images

# 3. Проверка контейнеров
docker ps -a

# 4. Проверка сетей
docker network ls

# 5. Проверка volumes
docker volume ls

# 6. Полная очистка (осторожно!)
docker-compose -f docker-compose.ip.yml down -v
docker system prune -a --volumes
```

## Скрипт для автоматической диагностики

Создайте `scripts/diagnose.sh`:

```bash
#!/bin/bash
echo "🔍 Диагностика Docker окружения..."

echo "1. Docker версия:"
docker --version
docker-compose --version

echo "2. Доступное место:"
df -h | grep -E '^/dev/'

echo "3. Docker образы:"
docker images | head -10

echo "4. Запущенные контейнеры:"
docker ps

echo "5. Сети:"
docker network ls

echo "6. Проверка доступности registry:"
curl -I https://registry-1.docker.io/v2/ 2>&1 | head -1

echo "✅ Диагностика завершена"
```

## Рекомендации для сервера

1. **Используйте внешний PostgreSQL/Redis** (если доступны):
   - Уберите postgres и redis из docker-compose
   - Укажите внешние хосты в DATABASE_URL и REDIS_URL

2. **Используйте build вместо pull** для backend/frontend:
   - Они уже настроены на локальную сборку

3. **Кешируйте образы**:
   ```bash
   # Сохраните образы
   docker save postgres:15-alpine redis:7-alpine > base-images.tar
   
   # На сервере загрузите
   docker load < base-images.tar
   ```

4. **Используйте .dockerignore** для ускорения сборки:
   - Уже настроен в проекте
