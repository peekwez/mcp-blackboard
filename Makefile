.PHONY: sync
sync:
	uv sync --all-extras --all-packages --group dev

.PHONY: format
format: 
	uv run ruff format
	uv run ruff check --fix

.PHONY: lint
lint: 
	uv run ruff check

.PHONY: mypy
mypy: 
	uv run mypy .

.PHONY: tests
tests: 
	uv run pytest 

.PHONY: coverage
coverage:
	
	uv run coverage run -m pytest
	uv run coverage xml -o coverage.xml
	uv run coverage report -m --fail-under=95

.PHONY: debug
debug:
	uv run src/main.py

.PHONY: build
build:
	docker build -t mcp-context-builder .

.PHONY: run
run::
	docker run -it --rm \
		--env-file .env \
		-p 8000:8000 \
		-v ./samples:/app/samples \
		--name mcp-context-builder \
		mcp-context-builder


inspect:
	npx @modelcontextprotocol/inspector \
		node build/index.js

.PHONY: clean
clean:
	docker system prune -f
	docker container prune -f
