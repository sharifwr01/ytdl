.PHONY: help install dev test clean docker-build docker-up docker-down logs backup restore

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements.txt

dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test: ## Run tests
	pytest --cov=. --cov-report=html --cov-report=term

test-watch: ## Run tests in watch mode
	ptw -- --cov=. --cov-report=term

lint: ## Run linters
	black --check .
	isort --check-only .
	flake8 .

format: ## Format code
	black .
	isort .

clean: ## Clean temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-restart: ## Restart Docker containers
	docker-compose restart

docker-logs: ## Show Docker logs
	docker-compose logs -f

docker-shell: ## Open shell in bot container
	docker-compose exec bot /bin/bash

docker-clean: ## Clean Docker resources
	docker-compose down -v
	docker system prune -af

db-migrate: ## Run database migrations
	alembic upgrade head

db-rollback: ## Rollback last migration
	alembic downgrade -1

db-shell: ## Open database shell
	docker-compose exec postgres psql -U ytbot -d ytbot

redis-shell: ## Open Redis shell
	docker-compose exec redis redis-cli

backup: ## Backup database
	@mkdir -p backup
	docker-compose exec -T postgres pg_dump -U ytbot ytbot > backup/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup created in backup/ directory"

restore: ## Restore database from backup (usage: make restore FILE=backup/backup_xxx.sql)
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Please specify backup file. Usage: make restore FILE=backup/backup_xxx.sql"; \
		exit 1; \
	fi
	docker-compose exec -T postgres psql -U ytbot ytbot < $(FILE)
	@echo "Database restored from $(FILE)"

setup: ## Initial setup (environment, database, etc.)
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file. Please edit it with your configuration."; \
	fi
	docker-compose up -d postgres redis
	@echo "Waiting for database to be ready..."
	@sleep 5
	$(MAKE) db-migrate
	@echo "Setup complete! Run 'make docker-up' to start the bot."

run-local: ## Run bot locally (not in Docker)
	python bot.py

deploy: ## Deploy to production
	git pull origin main
	docker-compose build --no-cache
	docker-compose up -d
	docker-compose logs --tail=50

status: ## Check service status
	docker-compose ps

monitor: ## Show resource usage
	docker stats

update: ## Update dependencies
	pip install --upgrade -r requirements.txt

security-check: ## Run security checks
	pip-audit
	bandit -r .

coverage: ## Generate coverage report
	pytest --cov=. --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"