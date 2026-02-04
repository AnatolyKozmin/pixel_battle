# 🚀 Быстрый запуск (без лишних выебонов)

## На сервере:

```bash
cd ~/ct/pixel_battle

# 1. Настройте IP (если нужно)
export ALLOWED_ORIGINS="http://YOUR_SERVER_IP:80,http://YOUR_SERVER_IP:8000"
export VITE_API_URL="http://YOUR_SERVER_IP:8000"
export VITE_WS_URL="ws://YOUR_SERVER_IP:8000"

# 2. Соберите образы ОДИН РАЗ
docker-compose build

# 3. Запустите (без --build, будет быстро!)
docker-compose up -d

# 4. Проверьте
docker-compose ps
curl http://localhost:8000/health
```

## Откройте в браузере:

```
http://YOUR_SERVER_IP:80
```

## Полезные команды:

```bash
# Остановка
docker-compose down

# Перезапуск (быстро, без пересборки)
docker-compose restart

# Логи
docker-compose logs -f

# Пересборка только если код изменился
docker-compose up -d --build
```

## ⚡ Оптимизация скорости:

1. **Соберите образы один раз**: `docker-compose build`
2. **Запускайте без --build**: `docker-compose up -d` (использует кеш)
3. **Пересборка только при изменениях**: `docker-compose up -d --build`

## 📝 Переменные окружения (опционально):

Создайте `.env` файл:

```bash
ALLOWED_ORIGINS=http://YOUR_SERVER_IP:80,http://YOUR_SERVER_IP:8000
VITE_API_URL=http://YOUR_SERVER_IP:8000
VITE_WS_URL=ws://YOUR_SERVER_IP:8000
```

Или просто экспортируйте перед запуском (см. выше).
