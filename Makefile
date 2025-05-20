.PHONY: sync format lint mypy tests coverage debug build run start stop inspect clean

all: down build clean up check

push:
	git push origin HEAD
	git push --tags

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
	uv run coverage html -d htmlcov
	uv run coverage report -m

link-path:
	mkdir -p /tmp/genai/data || true
	mkdir -p /tmp/genai/cache || true

link-data: link-path
	rm -fr /tmp/genai/data/samples || true
	cp -r $(shell pwd)/samples /tmp/genai/data/samples
	ls -l /tmp/genai/data/

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

down:
	docker compose down

up: down link-data
	docker compose up -d

check:
	docker compose ps

inspect:
	npx @modelcontextprotocol/inspector \
		node build/index.js

clean:
	docker system prune -f
	docker container prune -f
