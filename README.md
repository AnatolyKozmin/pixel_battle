# Pixel Battle - Telegram Mini App

Игра Pixel Battle реализована как Telegram Mini App с ботом для авторизации.

## Архитектура

### Backend
- **FastAPI** - основной фреймворк
- **WebSocket** - real-time обновления холста
- **PostgreSQL** - основное хранилище данных
- **Redis** - кеширование и pub/sub для синхронизации
- **Alembic** - миграции БД

### Frontend
- **Vue.js 3** - фронтенд фреймворк
- **Canvas API** - отрисовка пикселей
- **WebSocket Client** - подключение к серверу

### Telegram
- **Telegram Bot** - авторизация и уведомления
- **Telegram Mini App** - веб-интерфейс игры

## Структура проекта

```
pixel_battle/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   └── websocket/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── telegram/
│   ├── alembic/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
└── docker-compose.yml
```

## Особенности

- Real-time синхронизация через WebSocket
- Rate limiting для защиты от спама
- Кеширование холста в Redis
- Оптимизированные запросы к БД
- Поддержка горизонтального масштабирования
- **Docker контейнеризация** с поддержкой множественных инстансов
- **Kubernetes** манифесты для оркестрации
- **Автоматическое масштабирование** (HPA в Kubernetes)

## Установка и запуск

### Docker (рекомендуется)

#### Локальная разработка
```bash
# Запуск всех сервисов
docker-compose up -d

# Запуск миграций
docker-compose exec backend alembic upgrade head

# Просмотр логов
docker-compose logs -f
```

#### Production
```bash
# Использование Makefile (рекомендуется)
make build-prod
make up-prod
make migrate-prod

# Или напрямую
docker-compose -f docker-compose.prod.yml up -d
```

#### Масштабирование инстансов
```bash
# Docker Compose
docker-compose -f docker-compose.prod.yml up -d --scale backend=5

# Или через Makefile
make scale-backend REPLICAS=5

# Или через скрипт
./scripts/scale-backend.sh 5
```

#### Docker Swarm Mode
```bash
# Инициализация swarm
docker swarm init

# Деплой стека
docker stack deploy -c docker-compose.swarm.yml pixel_battle

# Масштабирование
docker service scale pixel_battle_backend=5
```

### Ручная установка

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Конфигурация

Создайте `.env` файл с необходимыми переменными окружения (см. `backend/.env.example`)

## Масштабирование

Проект поддерживает горизонтальное масштабирование:
- **Docker Compose**: Используйте `--scale` для увеличения инстансов
- **Docker Swarm**: Автоматическое распределение нагрузки
- **Kubernetes**: HPA для автоматического масштабирования (см. `k8s/`)

Подробнее в [DOCKER.md](DOCKER.md)
