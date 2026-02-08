# Решение проблем со сборкой Docker

## Ошибка: TLS handshake timeout при загрузке nginx:alpine

### Решение 1: Повторить попытку
Иногда это временная проблема сети:
```bash
docker compose -f docker-compose.local.yml up -d --build
```

### Решение 2: Предварительно загрузить образ
```bash
docker pull nginx:alpine
docker pull node:18-alpine
docker compose -f docker-compose.local.yml up -d --build
```

### Решение 3: Использовать другой тег nginx
Если проблема сохраняется, можно попробовать другой тег:
- `nginx:latest`
- `nginx:1.25-alpine`
- `nginx:1.24-alpine`

### Решение 4: Проверить настройки Docker
```bash
# Проверить DNS
docker info | grep -i dns

# Проверить прокси (если используется)
echo $HTTP_PROXY
echo $HTTPS_PROXY
```

### Решение 5: Очистить кэш Docker
```bash
docker system prune -a
docker compose -f docker-compose.local.yml build --no-cache
```

### Решение 6: Использовать локальный образ (если уже есть)
Если образ уже загружен локально:
```bash
docker images | grep nginx
# Если образ есть, Docker должен использовать его из кэша
```

### Решение 7: Проверить интернет-соединение
```bash
ping registry-1.docker.io
curl -I https://registry-1.docker.io
```

### Решение 8: Использовать альтернативный registry (если доступен)
Можно настроить Docker для использования альтернативного registry через `/etc/docker/daemon.json`
