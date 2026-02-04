.PHONY: help build up down restart logs scale-backend health deploy rollback

# Переменные
COMPOSE_FILE = docker-compose.yml
COMPOSE_PROD = docker-compose.prod.yml
ENV = dev

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Собрать образы
	docker-compose -f $(COMPOSE_FILE) build

build-prod: ## Собрать production образы
	docker-compose -f $(COMPOSE_PROD) build

up: ## Запустить все сервисы
	docker-compose -f $(COMPOSE_FILE) up -d

up-prod: ## Запустить production сервисы
	docker-compose -f $(COMPOSE_PROD) up -d

down: ## Остановить все сервисы
	docker-compose -f $(COMPOSE_FILE) down

down-prod: ## Остановить production сервисы
	docker-compose -f $(COMPOSE_PROD) down

restart: ## Перезапустить все сервисы
	docker-compose -f $(COMPOSE_FILE) restart

restart-prod: ## Перезапустить production сервисы
	docker-compose -f $(COMPOSE_PROD) restart

logs: ## Показать логи
	docker-compose -f $(COMPOSE_FILE) logs -f

logs-backend: ## Показать логи backend
	docker-compose -f $(COMPOSE_FILE) logs -f backend

logs-prod: ## Показать production логи
	docker-compose -f $(COMPOSE_PROD) logs -f

scale-backend: ## Масштабировать backend (использование: make scale-backend REPLICAS=3)
	@if [ -z "$(REPLICAS)" ]; then \
		echo "Использование: make scale-backend REPLICAS=3"; \
		exit 1; \
	fi
	docker-compose -f $(COMPOSE_PROD) up -d --scale backend=$(REPLICAS)

health: ## Проверка здоровья сервисов
	@./scripts/health-check.sh $(ENV)

deploy: ## Деплой приложения
	@./scripts/deploy.sh $(ENV)

rollback: ## Откат к предыдущей версии
	@./scripts/rollback.sh $(ENV)

migrate: ## Запустить миграции БД
	docker-compose -f $(COMPOSE_FILE) exec backend alembic upgrade head

migrate-prod: ## Запустить миграции БД (production)
	docker-compose -f $(COMPOSE_PROD) exec backend alembic upgrade head

shell-backend: ## Открыть shell в backend контейнере
	docker-compose -f $(COMPOSE_FILE) exec backend /bin/bash

shell-redis: ## Открыть shell в redis контейнере
	docker-compose -f $(COMPOSE_FILE) exec redis /bin/sh

ps: ## Показать статус контейнеров
	docker-compose -f $(COMPOSE_FILE) ps

ps-prod: ## Показать статус production контейнеров
	docker-compose -f $(COMPOSE_PROD) ps

clean: ## Очистить неиспользуемые образы и контейнеры
	docker system prune -f

clean-all: ## Очистить все (включая volumes)
	docker-compose -f $(COMPOSE_FILE) down -v
	docker system prune -af --volumes

stats: ## Показать статистику использования ресурсов
	docker stats

# Локальный запуск
start-local: ## Запустить локально (создаст .env файлы и запустит все)
	@./scripts/start-local.sh

stop-local: ## Остановить локальные сервисы
	docker-compose down

logs-local: ## Показать логи локальных сервисов
	docker-compose logs -f

# IP deployment команды
setup-ip: ## Настроить для запуска по IP (использование: make setup-ip IP=192.168.1.100)
	@if [ -z "$(IP)" ]; then \
		echo "Использование: make setup-ip IP=192.168.1.100"; \
		exit 1; \
	fi
	@./scripts/setup-ip.sh $(IP)

up-ip: ## Запустить по IP адресу
	docker-compose -f docker-compose.ip.yml up -d

down-ip: ## Остановить сервисы (IP)
	docker-compose -f docker-compose.ip.yml down

build-ip: ## Собрать образы для IP
	docker-compose -f docker-compose.ip.yml build

logs-ip: ## Показать логи (IP)
	docker-compose -f docker-compose.ip.yml logs -f

restart-ip: ## Перезапустить сервисы (IP)
	docker-compose -f docker-compose.ip.yml restart

# Kubernetes команды
k8s-apply: ## Применить Kubernetes манифесты
	kubectl apply -f k8s/

k8s-delete: ## Удалить Kubernetes ресурсы
	kubectl delete -f k8s/

k8s-scale: ## Масштабировать в Kubernetes (использование: make k8s-scale REPLICAS=5)
	@if [ -z "$(REPLICAS)" ]; then \
		echo "Использование: make k8s-scale REPLICAS=5"; \
		exit 1; \
	fi
	kubectl scale deployment pixel-battle-backend --replicas=$(REPLICAS)

k8s-logs: ## Показать логи Kubernetes pods
	kubectl logs -l app=pixel-battle-backend -f

k8s-status: ## Показать статус Kubernetes ресурсов
	kubectl get pods -l app=pixel-battle-backend
	kubectl get services
	kubectl get ingress
