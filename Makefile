.PHONY: sync format lint mypy tests coverage debug build run start stop inspect clean

all: down build clean up check

sync:
	uv sync --all-extras --all-packages --group dev

format:
	uv run ruff format
	uv run ruff check --fix

lint:
	uv run ruff check

mypy:
	uv run mypy .

tests:
	uv run pytest

coverage:
	uv run coverage run -m pytest
	uv run coverage xml -o coverage.xml
	uv run coverage report -m --fail-under=95



link-path:
	@echo "Linking path..."
	mkdir -p /tmp/genai/data || true
	mkdir -p /tmp/genai/cache || true

link-data: link-path
	unlink /tmp/genai/data/bb-samples || true
	ln -s $(shell pwd)/samples /tmp/genai/data/bb-samples
	ls -l /tmp/genai/data/bb-samples/

debug: link-data
	uv run src/main.py

build:
	docker build -t mcp/blackboard .

run: link-data
	docker run -it --rm \
		--env-file .env.docker \
		-p 8000:8000 \
		-v /tmp/genai/data:/app/data \
		-v /tmp/genai/cache:/app/cache \
		--name mcp-blackboard \
		mcp/blackboard

up: link-data
	docker compose up -d

down:
	docker compose down

check:
	docker compose ps

inspect:
	npx @modelcontextprotocol/inspector \
		node build/index.js

clean:
	docker system prune -f
	docker container prune -f
