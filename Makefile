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

debug:
	uv run src/main.py

build:
	docker build -t mcp/blackboard .

run:
	docker run -it --rm -d \
		--env-file .env \
		-p 8000:8000 \
		-v ./samples:/app/samples \
		--name mcp-blackboard \
		mcp/blackboard

up:
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
