# 🚀 Быстрый запуск по IP адресу

## Самый простой способ (5 минут)

### 1. На сервере:

```bash
# Склонируйте проект
git clone <your-repo>
cd pixel_battle

# Автоматическая настройка (замените на ваш IP)
./scripts/setup-ip.sh 192.168.1.100

# Или через Makefile
make setup-ip IP=192.168.1.100
```

### 2. Запуск:

```bash
# Через Makefile
make up-ip

# Или напрямую
docker-compose -f docker-compose.ip.yml up -d
```

### 3. Откройте в браузере:

```
http://192.168.1.100:80
```

Готово! 🎉

---

## Ручная настройка (если скрипт не работает)

### 1. Backend `.env`:

```env
ALLOWED_ORIGINS=http://YOUR_IP:5173,http://YOUR_IP:80,http://localhost:5173
```

### 2. Frontend `.env`:

```env
VITE_API_URL=http://YOUR_IP:8000
VITE_WS_URL=ws://YOUR_IP:8000
```

### 3. Запуск:

```bash
docker-compose -f docker-compose.ip.yml up -d
```

---

## Проверка работы

```bash
# Health check
curl http://YOUR_IP:8000/health

# Логи
docker-compose -f docker-compose.ip.yml logs -f

# Статус
docker-compose -f docker-compose.ip.yml ps
```

---

## ⚠️ Важно

1. **Telegram Mini App не будет работать** без HTTPS
2. **Используйте только для тестирования**
3. **Для production нужен HTTPS**

---

## 🔧 Troubleshooting

### CORS ошибки?
- Проверьте `ALLOWED_ORIGINS` в backend `.env`
- Должен включать ваш IP

### WebSocket не работает?
- Используйте `ws://` (не `wss://`)
- Проверьте порт 8000

### Не могу подключиться?
- Проверьте firewall: `sudo ufw allow 8000/tcp`
- Проверьте, что сервис слушает на `0.0.0.0`
