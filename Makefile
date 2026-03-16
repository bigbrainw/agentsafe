.PHONY: help setup test otel-up otel-down clear-jaegar demo-otel-hidden demo-otel-visible demo-observability

help:
	@echo "Available targets:"
	@echo "  make setup              - Install project deps (dev + openai + otel)"
	@echo "  make test               - Run test suite"
	@echo "  make otel-up            - Start local Jaeger OTEL stack"
	@echo "  make otel-down          - Stop local Jaeger OTEL stack"
	@echo "  make clear-jaegar       - Stop and remove local Jaeger OTEL volumes"
	@echo "  make demo-observability - Run observability demo"
	@echo "  make demo-otel-hidden   - Run OTEL demo with content hidden in Jaeger"
	@echo "  make demo-otel-visible  - Run OTEL demo with prompt/response snippets in Jaeger"

setup:
	uv sync --extra dev --extra openai --extra otel

test:
	.venv/bin/python -m pytest -q

otel-up:
	docker compose -f docker-compose.otel.yml up -d

otel-down:
	docker compose -f docker-compose.otel.yml down

clear-jaegar:
	docker compose -f docker-compose.otel.yml down -v --remove-orphans

demo-observability:
	uv run python examples/observability_demo.py

demo-otel-hidden:
	AGENTSAFE_OTEL_INCLUDE_CONTENT=false uv run python examples/local_otel_openai_demo.py

demo-otel-visible:
	AGENTSAFE_OTEL_INCLUDE_CONTENT=true uv run python examples/local_otel_openai_demo.py
