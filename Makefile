DC = docker compose

CMD = uv run

EXEC_CMD = $(DC) exec backend

EXEC_DJANGO = $(EXEC_CMD) python backend/manage.py

.PHONY: help up down stop start restart build logs logs-backend logs-bot logs-celery migrate makemigrations superuser shell bash-backend lint format types qa

help:
	@echo "\033[33mUsage:\033[0m make [command]"
	@echo ""
	@echo "\033[32mDocker Controls:\033[0m"
	@echo "  \033[36mup\033[0m              Start project in background"
	@echo "  \033[36mdown\033[0m            Stop and remove containers"
	@echo "  \033[36mrestart\033[0m         Restart all containers"
	@echo "  \033[36mbuild\033[0m           Rebuild and start"
	@echo ""
	@echo "\033[32mLogs:\033[0m"
	@echo "  \033[36mlogs\033[0m            Show all logs"
	@echo ""
	@echo "\033[32mDjango:\033[0m"
	@echo "  \033[36mmigrate\033[0m         Apply migrations"
	@echo "  \033[36mmakemigrations\033[0m  Create migrations"
	@echo "  \033[36msuperuser\033[0m       Create superuser"
	@echo "  \033[36mshell\033[0m           Django Shell"
	@echo ""
	@echo "\033[32mQuality:\033[0m"
	@echo "  \033[36mlint\033[0m            Check code style (Ruff)"
	@echo "  \033[36mformat\033[0m          Fix code style (Ruff)"
	@echo "  \033[36mtypes\033[0m           Check types (Mypy)"
	@echo "  \033[36mqa\033[0m              Run ALL checks"

up:
	$(DC) up -d

down:
	$(DC) down

stop:
	$(DC) stop

start:
	$(DC) start

restart: down up

build:
	$(DC) up --build -d

logs:
	$(DC) logs -f

logs-backend:
	$(DC) logs -f backend

logs-bot:
	$(DC) logs -f bot

logs-celery:
	$(DC) logs -f celery

migrate:
	$(EXEC_DJANGO) migrate

makemigrations:
	$(EXEC_DJANGO) makemigrations

superuser:
	$(EXEC_DJANGO) createsuperuser

shell:
	$(EXEC_DJANGO) shell

bash-backend:
	$(EXEC_CMD) bash

init-tasks:
	docker compose exec backend python backend/manage.py setup_periodic_tasks

lint:
	@echo "Running Ruff Linter..."
	$(CMD) ruff check .

format:
	@echo "Running Ruff Formatter..."
	$(CMD) ruff format .

types:
	@echo "Running Mypy..."
	PYTHONPATH=backend $(CMD) mypy backend bot

qa: format lint types
	@echo "✅ QA Checks Completed!"