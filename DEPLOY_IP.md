# Запуск на удаленном сервере по IP (без HTTPS)

## ⚠️ Важные замечания

1. **Telegram Mini App требует HTTPS** - для полноценной работы с Telegram нужен SSL
2. **Для тестирования** можно запустить обычный веб-интерфейс по IP
3. **WebSocket** будет работать по `ws://` вместо `wss://`

## 🚀 Быстрый запуск

### Вариант 1: Docker Compose (рекомендуется)

1. **На сервере** склонируйте проект:
```bash
git clone <your-repo>
cd pixel_battle
```

2. **Создайте `.env` файл**:
```bash
cd backend
cp .env.example .env
nano .env
```

Настройте:
```env
# Database (используйте внешний PostgreSQL или в Docker)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/pixel_battle

# Redis (или в Docker)
REDIS_URL=redis://localhost:6379/0

# Telegram (можно оставить пустым для теста)
TELEGRAM_BOT_TOKEN=your_token
APP_SECRET_KEY=your_secret_key

# CORS - ВАЖНО! Добавьте IP сервера
ALLOWED_ORIGINS=http://YOUR_SERVER_IP:5173,http://YOUR_SERVER_IP:80,http://localhost:5173
```

3. **Запустите через Docker Compose**:
```bash
# Из корня проекта
docker-compose up -d
```

4. **Откройте в браузере**:
```
http://YOUR_SERVER_IP:80
```

### Вариант 2: Ручной запуск

#### Backend:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Настройте .env
nano .env

# Запустите миграции
alembic upgrade head

# Запустите сервер (слушаем на всех интерфейсах)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Frontend:

```bash
cd frontend
npm install

# Создайте .env
echo "VITE_API_URL=http://YOUR_SERVER_IP:8000" > .env
echo "VITE_WS_URL=ws://YOUR_SERVER_IP:8000" >> .env

# Запустите dev сервер (для production используйте build)
npm run dev -- --host 0.0.0.0 --port 5173
```

Откройте: `http://YOUR_SERVER_IP:5173`

---

## 🔧 Настройка для работы по IP

### 1. Обновить CORS настройки

В `backend/app/core/config.py` или `.env`:
```python
ALLOWED_ORIGINS=http://YOUR_SERVER_IP:5173,http://YOUR_SERVER_IP:80,http://YOUR_SERVER_IP:8080
```

### 2. Обновить frontend переменные

В `frontend/.env`:
```env
VITE_API_URL=http://YOUR_SERVER_IP:8000
VITE_WS_URL=ws://YOUR_SERVER_IP:8000
```

### 3. Настроить firewall

```bash
# Открыть порты
sudo ufw allow 8000/tcp  # Backend API
sudo ufw allow 5173/tcp  # Frontend dev
sudo ufw allow 80/tcp    # Frontend production
sudo ufw allow 443/tcp   # HTTPS (если будет)
```

---

## 🐳 Docker Compose для IP

Создайте `docker-compose.ip.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: pixel_battle
      POSTGRES_USER: pixel_user
      POSTGRES_PASSWORD: pixel_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+asyncpg://pixel_user:pixel_pass@postgres:5432/pixel_battle
      REDIS_URL: redis://redis:6379/0
      TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN}
      APP_SECRET_KEY: ${APP_SECRET_KEY}
      ALLOWED_ORIGINS: http://YOUR_SERVER_IP:5173,http://YOUR_SERVER_IP:80,http://localhost:5173
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis

  frontend:
    build:
      context: ./frontend
      args:
        - VITE_API_URL=http://YOUR_SERVER_IP:8000
        - VITE_WS_URL=ws://YOUR_SERVER_IP:8000
    ports:
      - "80:80"

volumes:
  postgres_data:
  redis_data:
```

Запуск:
```bash
docker-compose -f docker-compose.ip.yml up -d
```

---

## 🔒 Безопасность (важно!)

### Для production НЕ используйте IP без HTTPS:

1. **Telegram Mini App требует HTTPS**
2. **WebSocket без SSL небезопасен**
3. **Данные передаются в открытом виде**

### Временное решение для тестирования:

1. Используйте только для разработки/тестирования
2. Не передавайте реальные данные пользователей
3. Ограничьте доступ через firewall (только ваши IP)

### Быстрое HTTPS решение:

#### Вариант 1: Cloudflare Tunnel (бесплатно)
```bash
# Установите cloudflared
# Создайте туннель
cloudflared tunnel --url http://localhost:80
```

#### Вариант 2: Let's Encrypt (бесплатный SSL)
```bash
# Установите certbot
sudo apt install certbot

# Получите сертификат (нужен домен)
sudo certbot certonly --standalone -d your-domain.com
```

#### Вариант 3: Nginx с самоподписанным сертификатом (для теста)
```bash
# Генерируем сертификат
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/key.pem \
  -out /etc/nginx/ssl/cert.pem

# Настраиваем Nginx (см. nginx/nginx.prod.conf)
```

---

## 📝 Чеклист для запуска по IP

- [ ] Настроить `.env` файлы (backend и frontend)
- [ ] Добавить IP в `ALLOWED_ORIGINS`
- [ ] Обновить `VITE_API_URL` и `VITE_WS_URL` в frontend
- [ ] Открыть порты в firewall
- [ ] Запустить сервисы (Docker или вручную)
- [ ] Проверить доступность: `http://YOUR_SERVER_IP:8000/health`
- [ ] Открыть в браузере: `http://YOUR_SERVER_IP:80` или `:5173`

---

## 🐛 Troubleshooting

### Проблема: CORS ошибки

**Решение**: Проверьте `ALLOWED_ORIGINS` в `.env` - должен включать IP сервера

### Проблема: WebSocket не подключается

**Решение**: 
- Используйте `ws://` вместо `wss://`
- Проверьте, что порт 8000 открыт
- Проверьте `VITE_WS_URL` в frontend `.env`

### Проблема: Не могу подключиться к серверу

**Решение**:
```bash
# Проверьте firewall
sudo ufw status

# Проверьте, что сервис слушает на 0.0.0.0
netstat -tulpn | grep :8000

# Проверьте доступность
curl http://YOUR_SERVER_IP:8000/health
```

### Проблема: Telegram Mini App не работает

**Решение**: Это нормально! Telegram требует HTTPS. Для тестирования используйте обычный браузер без Telegram интеграции.

---

## 🎯 Рекомендации

1. **Для разработки**: Используйте IP + порты (быстро, но небезопасно)
2. **Для тестирования**: Используйте Cloudflare Tunnel (бесплатный HTTPS)
3. **Для production**: Обязательно HTTPS + домен + Let's Encrypt

---

## 📚 Полезные команды

```bash
# Проверить открытые порты
sudo netstat -tulpn

# Проверить firewall
sudo ufw status

# Проверить логи Docker
docker-compose logs -f

# Перезапустить сервисы
docker-compose restart

# Остановить все
docker-compose down
```
