stop: ## Останавливает докер-сервисы
	docker compose down
	@echo "Сервисы успешно остановлены"

start: ## Запускает докер-сервисы
	docker compose up --build -d
	@echo "Сервисы успешно запущены"

update: ## Обновляет докер-сервисы
	docker compose pull --ignore-buildable
	docker compose build
	@echo "Сервисы успешно обновлены"

migrations: ## Накатывает миграции
	alembic revision --autogenerate
	@echo "Миграции успешно накатаны"

migrate: ## Применяет миграции
	alembic upgrade head
	@echo "Миграции успешно применены"

help: ## Отображает список доступных команд и их описания
	@echo "Cписок доступных команд:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
