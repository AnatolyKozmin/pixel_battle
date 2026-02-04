# 🚀 Запуск на сервере - Пошаговая инструкция

## Шаг 1: Настройка IP (если еще не сделано)

```bash
cd ~/ct/pixel_battle

# Замените YOUR_SERVER_IP на реальный IP вашего сервера
./scripts/setup-ip.sh YOUR_SERVER_IP

# Или вручную отредактируйте docker-compose.ip.yml:
# Замените все YOUR_SERVER_IP на ваш IP
```

**Как узнать IP сервера:**
```bash
# Вариант 1: Внешний IP
curl ifconfig.me

# Вариант 2: Локальный IP
hostname -I | awk '{print $1}'

# Вариант 3: Все IP
ip addr show
```

## Шаг 2: Запуск всех сервисов

```bash
# Сборка и запуск
docker-compose -f docker-compose.ip.yml up -d --build

# Или пошагово:
# 1. Сборка образов
docker-compose -f docker-compose.ip.yml build

# 2. Запуск
docker-compose -f docker-compose.ip.yml up -d
```

## Шаг 3: Проверка

```bash
# Проверка статуса всех контейнеров
docker-compose -f docker-compose.ip.yml ps

# Должны быть запущены:
# - pixel_battle_postgres_ip (healthy)
# - pixel_battle_redis_ip (healthy)
# - pixel_battle_backend_ip (healthy)
# - pixel_battle_frontend_ip (healthy)
```

## Шаг 4: Проверка логов

```bash
# Все логи
docker-compose -f docker-compose.ip.yml logs -f

# Логи конкретного сервиса
docker-compose -f docker-compose.ip.yml logs -f backend
docker-compose -f docker-compose.ip.yml logs -f frontend
docker-compose -f docker-compose.ip.yml logs -f postgres
```

## Шаг 5: Health check

```bash
# Проверка backend
curl http://localhost:8000/health
# Должен вернуть: {"status":"ok"}

# Проверка frontend
curl http://localhost:80
# Должен вернуть HTML страницу
```

## Шаг 6: Откройте в браузере

```
http://YOUR_SERVER_IP:80
```

## 🔧 Полезные команды

### Остановка
```bash
docker-compose -f docker-compose.ip.yml down
```

### Перезапуск
```bash
docker-compose -f docker-compose.ip.yml restart
```

### Пересборка после изменений
```bash
docker-compose -f docker-compose.ip.yml up -d --build
```

### Просмотр логов
```bash
# Все логи
docker-compose -f docker-compose.ip.yml logs -f

# Последние 100 строк
docker-compose -f docker-compose.ip.yml logs --tail=100

# Конкретный сервис
docker-compose -f docker-compose.ip.yml logs -f backend
```

### Выполнение команд в контейнере
```bash
# В backend контейнере
docker-compose -f docker-compose.ip.yml exec backend bash

# Запуск миграций вручную
docker-compose -f docker-compose.ip.yml exec backend alembic upgrade head

# Проверка подключения к БД
docker-compose -f docker-compose.ip.yml exec backend python -c "from app.core.database import engine; print('OK')"
```

## 🐛 Troubleshooting

### Backend не запускается

```bash
# Проверьте логи
docker-compose -f docker-compose.ip.yml logs backend

# Частые причины:
# 1. База данных не создана - entrypoint.sh должен создать автоматически
# 2. Миграции не выполнены - entrypoint.sh должен выполнить автоматически
# 3. Неправильный DATABASE_URL

# Ручной запуск миграций
docker-compose -f docker-compose.ip.yml exec backend alembic upgrade head
```

### Frontend не открывается

```bash
# Проверьте логи
docker-compose -f docker-compose.ip.yml logs frontend

# Проверьте, что порт 80 открыт
sudo ufw allow 80/tcp
sudo ufw allow 8000/tcp

# Проверьте, что frontend собран
docker-compose -f docker-compose.ip.yml ps frontend
```

### CORS ошибки

```bash
# Убедитесь, что ALLOWED_ORIGINS включает ваш IP
# В docker-compose.ip.yml должно быть:
ALLOWED_ORIGINS: http://YOUR_SERVER_IP:80,http://YOUR_SERVER_IP:8000

# Перезапустите backend
docker-compose -f docker-compose.ip.yml restart backend
```

### Порты заняты

```bash
# Проверьте занятые порты
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :5432

# Остановите конфликтующие сервисы или измените порты в docker-compose
```

## 📋 Полная последовательность команд

```bash
# 1. Перейти в директорию
cd ~/ct/pixel_battle

# 2. Настроить IP (замените на ваш IP)
./scripts/setup-ip.sh YOUR_SERVER_IP

# 3. Запустить
docker-compose -f docker-compose.ip.yml up -d --build

# 4. Проверить статус
docker-compose -f docker-compose.ip.yml ps

# 5. Проверить логи
docker-compose -f docker-compose.ip.yml logs -f

# 6. Health check
curl http://localhost:8000/health

# 7. Открыть в браузере
# http://YOUR_SERVER_IP:80
```

## ✅ Готово!

После выполнения всех шагов приложение должно быть доступно по адресу:
```
http://YOUR_SERVER_IP:80
```
