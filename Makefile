SHELL := /bin/bash

COMPOSE_DIR := infra/compose
COMPOSE := docker compose -f $(COMPOSE_DIR)/docker-compose.yml

OLLAMA_CONTAINER := ollama
OLLAMA_MODEL ?= llama3.1:8b

.DEFAULT_GOAL := help

.PHONY: help init up up-d build down down-v restart ps status health logs logs-librechat logs-ollama logs-mcp \
        pull-model list-models clean mcp-test librechat-url ollama-url test test-unit test-integration

help: ## Show available commands
	@echo ""
	@echo "Pokemon monorepo commands"
	@echo ""
	@awk 'BEGIN {FS = ":.*## "}; /^[a-zA-Z0-9_.-]+:.*## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

init: ## Prepare LibreChat .env from template if missing
	@if [ ! -f apps/librechat/.env ]; then \
		cp apps/librechat/.env.example apps/librechat/.env; \
		echo "Created apps/librechat/.env from .env.example"; \
	else \
		echo "apps/librechat/.env already exists"; \
	fi

build: ## Build all Docker services
	$(COMPOSE) build

up: ## Start the full stack in foreground
	$(COMPOSE) up --build

up-d: ## Start the full stack in background
	$(COMPOSE) up --build -d

down: ## Stop the full stack
	$(COMPOSE) down

down-v: ## Stop the full stack and remove volumes
	$(COMPOSE) down -v

restart: ## Restart the full stack
	$(COMPOSE) down
	$(COMPOSE) up --build -d

ps: ## Show running services
	$(COMPOSE) ps

status: ## Show stack status, key URLs, and installed Ollama models
	@echo ""
	@echo "=== Docker services ==="
	@$(COMPOSE) ps || true
	@echo ""
	@echo "=== URLs ==="
	@echo "LibreChat:   http://localhost:3080"
	@echo "Ollama:      http://localhost:11434"
	@echo "Pokemon MCP: http://localhost:8000/mcp"
	@echo ""
	@echo "=== Ollama models ==="
	@docker exec $(OLLAMA_CONTAINER) ollama list 2>/dev/null || echo "Ollama container not ready"
	@echo ""

health: ## Run quick health checks for LibreChat, Ollama, and Pokemon MCP
	@echo ""
	@echo "=== LibreChat ==="
	@code=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3080 || true); \
	if [ "$$code" = "200" ] || [ "$$code" = "302" ] || [ "$$code" = "304" ]; then \
		echo "OK  LibreChat responded with HTTP $$code"; \
	else \
		echo "ERR LibreChat responded with HTTP $$code"; \
	fi
	@echo ""
	@echo "=== Ollama ==="
	@code=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:11434/api/tags || true); \
	if [ "$$code" = "200" ]; then \
		echo "OK  Ollama responded with HTTP $$code"; \
	else \
		echo "ERR Ollama responded with HTTP $$code"; \
	fi
	@echo ""
	@echo "=== Pokemon MCP ==="
	@code=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/mcp || true); \
	if [ -n "$$code" ] && [ "$$code" != "000" ]; then \
		echo "OK  Pokemon MCP responded with HTTP $$code"; \
	else \
		echo "ERR Pokemon MCP did not respond"; \
	fi
	@echo ""

logs: ## Tail logs for all services
	$(COMPOSE) logs -f --tail=100

logs-librechat: ## Tail LibreChat logs
	$(COMPOSE) logs -f --tail=100 librechat

logs-ollama: ## Tail Ollama logs
	$(COMPOSE) logs -f --tail=100 ollama

logs-mcp: ## Tail pokemon-mcp logs
	$(COMPOSE) logs -f --tail=100 pokemon-mcp

pull-model: ## Pull an Ollama model. Override with: make pull-model OLLAMA_MODEL=qwen2.5:7b
	docker exec -it $(OLLAMA_CONTAINER) ollama pull $(OLLAMA_MODEL)

list-models: ## List models installed in Ollama
	docker exec -it $(OLLAMA_CONTAINER) ollama list

test: ## Run all tests inside the pokemon-mcp container
	$(COMPOSE) exec -T pokemon-mcp pytest -q

test-unit: ## Run unit tests only inside the pokemon-mcp container
	$(COMPOSE) exec -T pokemon-mcp pytest -q -m "not integration"

test-integration: ## Run integration tests only inside the pokemon-mcp container
	$(COMPOSE) exec -T pokemon-mcp pytest -q -m integration

librechat-url: ## Print LibreChat URL
	@echo "http://localhost:3080"

ollama-url: ## Print Ollama URL
	@echo "http://localhost:11434"

clean: ## Stop stack and remove volumes
	$(COMPOSE) down -v