# 🚀 Быстрый запуск локально

## Вариант 1: Docker Compose (самый простой)

### 1. Проверьте, что Docker установлен:

```bash
docker --version
docker-compose --version
```

### 2. Создайте .env файлы:

```bash
# Backend .env
cd backend
cp .env.example .env
# Отредактируйте .env (минимум нужно указать DATABASE_URL, REDIS_URL, TELEGRAM_BOT_TOKEN, APP_SECRET_KEY)
```

Минимальная настройка для локального запуска:
```env
DATABASE_URL=postgresql+asyncpg://pixel_user:pixel_pass@postgres:5432/pixel_battle
REDIS_URL=redis://redis:6379/0
TELEGRAM_BOT_TOKEN=your_token_here
APP_SECRET_KEY=local-dev-secret-key-change-in-production
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:80
```

```bash
# Frontend .env
cd ../frontend
echo "VITE_API_URL=http://localhost:8000" > .env
echo "VITE_WS_URL=ws://localhost:8000" >> .env
```

### 3. Запустите через Docker Compose:

```bash
# Из корня проекта
cd ..
docker-compose up -d

# Или с пересборкой
docker-compose up -d --build
```

### 4. Запустите миграции:

```bash
docker-compose exec backend alembic upgrade head
```

### 5. Откройте в браузере:

```
http://localhost:80
```

---

## Вариант 2: Ручной запуск (без Docker)

### Требования:
- Python 3.11+
- Node.js 18+
- PostgreSQL (или используйте Docker только для БД)
- Redis (или используйте Docker только для Redis)

### Backend:

```bash
cd backend

# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

# Установите зависимости
pip install -r requirements.txt

# Настройте .env
cp .env.example .env
# Отредактируйте .env

# Запустите миграции
alembic upgrade head

# Запустите сервер
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend:

```bash
cd frontend

# Установите зависимости
npm install

# Создайте .env
echo "VITE_API_URL=http://localhost:8000" > .env
echo "VITE_WS_URL=ws://localhost:8000" >> .env

# Запустите dev сервер
npm run dev
```

Откройте: `http://localhost:5173`

---

## Вариант 3: Смешанный (БД в Docker, приложение вручную)

### 1. Запустите только БД и Redis:

```bash
docker-compose up -d postgres redis
```

### 2. Запустите backend вручную:

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### 3. Запустите frontend вручную:

```bash
cd frontend
npm run dev
```

---

## 🔍 Проверка работы

### Health check:

```bash
curl http://localhost:8000/health
```

Должен вернуть: `{"status":"ok"}`

### Логи:

```bash
# Docker
docker-compose logs -f

# Backend (если вручную)
# Логи будут в терминале

# Frontend (если вручную)
# Логи будут в терминале
```

---

## 🐛 Troubleshooting

### Порт занят?

```bash
# Проверить, что использует порт
lsof -i :8000
lsof -i :5173
lsof -i :80

# Остановить процесс или изменить порт в docker-compose.yml
```

### Ошибка подключения к БД?

```bash
# Проверить, что PostgreSQL запущен
docker-compose ps postgres

# Проверить логи
docker-compose logs postgres
```

### CORS ошибки?

Проверьте `ALLOWED_ORIGINS` в `backend/.env` - должен включать `http://localhost:5173`

---

## 📝 Быстрая команда для первого запуска

```bash
# Создать .env файлы
cd backend && cp .env.example .env && cd ..
cd frontend && echo "VITE_API_URL=http://localhost:8000" > .env && echo "VITE_WS_URL=ws://localhost:8000" >> .env && cd ..

# Запустить через Docker
docker-compose up -d --build

# Миграции
docker-compose exec backend alembic upgrade head

# Открыть в браузере
open http://localhost:80  # macOS
# или
xdg-open http://localhost:80  # Linux
```

---

## 🎯 Что дальше?

После запуска:
1. Откройте `http://localhost:80` в браузере
2. Попробуйте разместить пиксель
3. Проверьте WebSocket (должны видеть обновления в реальном времени)

**Примечание**: Telegram Mini App не будет работать локально без HTTPS, но обычный веб-интерфейс будет работать!
