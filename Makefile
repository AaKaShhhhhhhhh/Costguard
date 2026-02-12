.PHONY: help install dev test lint format clean deploy docker-up docker-down

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install:  ## Install all dependencies
	pip install -e .
	cd mcp-servers/aws-cost-server && pip install -e . || true
	cd mcp-servers/llm-tracker-server && pip install -e . || true
	npm install -g @modelcontextprotocol/inspector || true

dev:  ## Start development environment
	docker-compose up -d
	uvicorn backend.api.main:app --reload &
	streamlit run ui/dashboard.py

test:  ## Run tests with coverage
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

lint:  ## Run linters
	ruff check .
	mypy .

format:  ## Auto-format code
	black .
	ruff check --fix .

clean:  ## Clean cache and build files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf dist build *.egg-info

deploy:  ## Deploy to Archestra.AI
	./scripts/deploy.sh

docker-up:  ## Start Docker containers
	docker-compose up -d

docker-down:  ## Stop Docker containers
	docker-compose down
