# Docker и развертывание инстансов

## Быстрый старт

### Локальная разработка

1. Создайте `.env` файл с необходимыми переменными
2. Запустите все сервисы:
```bash
docker-compose up -d
```

3. Запустите миграции:
```bash
docker-compose exec backend alembic upgrade head
```

4. Проверьте статус:
```bash
docker-compose ps
```

### Production

1. Используйте production compose файл:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

2. Или используйте скрипт деплоя:
```bash
./scripts/deploy.sh prod
```

## Масштабирование инстансов

### Docker Compose

#### Увеличение количества backend инстансов:

```bash
# Масштабирование до 4 инстансов
docker-compose -f docker-compose.prod.yml up -d --scale backend=4
```

#### Использование скрипта:

```bash
# Масштабирование до 5 инстансов
./scripts/scale-backend.sh 5
```

### Kubernetes

#### Применение манифестов:

```bash
# Создание секретов
kubectl create secret generic pixel-battle-secrets \
  --from-literal=database-url="postgresql+asyncpg://..." \
  --from-literal=telegram-bot-token="..." \
  --from-literal=app-secret-key="..."

# Применение манифестов
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/ingress.yaml
```

#### Масштабирование в Kubernetes:

```bash
# Ручное масштабирование
kubectl scale deployment pixel-battle-backend --replicas=5

# Автоматическое масштабирование (HPA)
# Настроено в deployment.yaml
# Минимум: 2, Максимум: 10
# Масштабируется по CPU (70%) и Memory (80%)
```

## Управление инстансами

### Просмотр статуса

```bash
# Docker Compose
docker-compose ps

# Kubernetes
kubectl get pods -l app=pixel-battle-backend
```

### Логи

```bash
# Docker Compose - все инстансы
docker-compose logs -f backend

# Docker Compose - конкретный инстанс
docker-compose logs -f backend_1

# Kubernetes
kubectl logs -l app=pixel-battle-backend -f
```

### Перезапуск

```bash
# Docker Compose
docker-compose restart backend

# Kubernetes
kubectl rollout restart deployment pixel-battle-backend
```

### Обновление

```bash
# Docker Compose
docker-compose build backend
docker-compose up -d backend

# Kubernetes (rolling update)
kubectl set image deployment/pixel-battle-backend \
  backend=pixel-battle-backend:new-version
```

## Мониторинг инстансов

### Health checks

```bash
# Проверка здоровья всех сервисов
./scripts/health-check.sh prod

# Проверка конкретного инстанса
curl http://localhost:8000/health
```

### Метрики

- **Docker**: `docker stats`
- **Kubernetes**: `kubectl top pods`

## Load Balancing

### Nginx (Docker Compose)

Настроен автоматически в `nginx/nginx.prod.conf`:
- Использует `least_conn` алгоритм
- Health checks для backend инстансов
- WebSocket поддержка

### Kubernetes Ingress

Настроен в `k8s/ingress.yaml`:
- Автоматический load balancing
- SSL termination
- WebSocket поддержка

## Рекомендации по масштабированию

### Когда увеличивать инстансы:

1. **CPU утилизация > 70%**
2. **Memory утилизация > 80%**
3. **Response time > 500ms**
4. **Очередь запросов растет**

### Оптимальное количество инстансов:

- **Минимум**: 2 (для отказоустойчивости)
- **Рекомендуется**: 3-5 для 1000 пользователей
- **Максимум**: Зависит от ресурсов сервера

### Формула расчета:

```
Инстансы = (Пиковая нагрузка * Время ответа) / (Время ответа цели)
```

Пример:
- Пиковая нагрузка: 100 RPS
- Время ответа: 200ms
- Целевое время: 100ms
- Инстансы = (100 * 0.2) / 0.1 = 2 инстанса

## Troubleshooting

### Инстансы не запускаются

```bash
# Проверка логов
docker-compose logs backend

# Проверка ресурсов
docker stats

# Проверка конфигурации
docker-compose config
```

### Инстансы не синхронизируются

- Проверьте Redis подключение
- Проверьте REDIS_PUBSUB_CHANNEL
- Проверьте сеть между контейнерами

### Высокая нагрузка на один инстанс

- Проверьте load balancer конфигурацию
- Проверьте health checks
- Убедитесь, что все инстансы здоровы

## Автоматическое масштабирование (Kubernetes HPA)

HPA автоматически масштабирует инстансы на основе:
- CPU утилизации (цель: 70%)
- Memory утилизации (цель: 80%)

Настройки в `k8s/deployment.yaml`:
- Минимум: 2 инстанса
- Максимум: 10 инстансов
- Масштабирование вверх: до 100% за 15 секунд
- Масштабирование вниз: до 50% за 60 секунд

## Blue-Green Deployment

Для zero-downtime обновлений:

```bash
# 1. Развернуть новую версию
docker-compose -f docker-compose.prod.yml up -d --scale backend=4

# 2. Проверить новую версию
curl http://localhost:8000/health

# 3. Обновить load balancer конфигурацию

# 4. Остановить старую версию
docker-compose -f docker-compose.prod.yml up -d --scale backend=2
```

## Откат (Rollback)

```bash
# Использование скрипта
./scripts/rollback.sh prod

# Или вручную
docker-compose -f docker-compose.prod.yml down
# Восстановить из бэкапа
docker-compose -f docker-compose.prod.yml up -d
```
