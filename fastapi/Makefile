.PHONY: help install dev db-up db-down db-reset migrate migrate-create test clean format lint run

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install pytest pytest-asyncio black flake8 mypy

db-up: ## Start PostgreSQL with Docker
	docker-compose up -d
	@echo "Waiting for database to be ready..."
	@timeout 10

db-down: ## Stop PostgreSQL
	docker-compose down

db-reset: ## Reset database (WARNING: destroys all data)
	docker-compose down -v
	docker-compose up -d
	@echo "Waiting for database to be ready..."
	@timeout 10

db-logs: ## Show database logs
	docker-compose logs -f postgres

migrate: ## Run database migrations
	alembic upgrade head

migrate-create: ## Create new migration (use MSG="description")
	alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Rollback last migration
	alembic downgrade -1

migrate-history: ## Show migration history
	alembic history

run: ## Run the application
	uvicorn app.main:app --reload

run-prod: ## Run in production mode
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

test: ## Run tests
	pytest

format: ## Format code with black
	black app/

lint: ## Lint code
	flake8 app/
	mypy app/

clean: ## Clean up cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
