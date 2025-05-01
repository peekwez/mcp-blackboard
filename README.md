# mcp-blackboard

> **Version 0.1.0** – A lightweight blackboard memory server for the **Model Context Protocol (MCP)**

`mcp-blackboard` exposes a simple HTTP/SSE interface that lets multiple AI agents **store, and retrieve context and results**—documents, embeddings, structured objects, and more—on a shared “blackboard”.

It is designed to be dropped into any MCP‑compatible workflow so your planner,
researcher, extractor, analyzer, writer, editor, and evaluator agents can collaborate without reinventing persistence.

<div align="center">
<img src="https://img.shields.io/badge/Python-3.12%2B-blue" />
<img src="https://img.shields.io/badge/License-MIT-green" />
<img src="https://img.shields.io/badge/Protocol-MCP-informational" />
</div>

---

## Available Tools

### MCP Tools

The following tools are available in `mcp-blackboard`:

- **`save_plan(plan_id: str, plan: dict | str) -> str`**  
   Save a plan to the shared state.

- **`mark_plan_as_completed(plan_id: str, step_id: str) -> str`**  
   Mark a plan step as completed in the shared state.

- **`save_result(plan_id: str, agent_name: str, step_id: str, description: str, result: str | dict) -> str`**  
   Save a result to the shared state.

- **`save_context_description(plan_id: str, file_path_or_url: str, description: str) -> str`**  
   Write a context description to the shared state.

- **`get_blackboard(plan_id: str) -> str | dict | None`**  
   Fetch a blackboard entry for a plan.

- **`get_plan(plan_id: str) -> str | dict | None`**  
   Fetch a plan from the shared state.

- **`get_result(plan_id: str, agent_name: str, step_id: str) -> str | dict | None`**  
   Fetch a result from the shared state.

- **`get_context(file_path_or_url: str, use_cache: bool = True) -> str`**  
   Read and convert media content to Markdown format.

### File Cache Management Scheduler

- **`remove_stale_files(max_age: int = 3600) -> None`**  
  Remove files older than the specified age from the cache directory.

## ✨ Highlights

| Capability                  | Why it matters                                                                                  |
| --------------------------- | ----------------------------------------------------------------------------------------------- |
| **Unified memory**          | One source of truth for agent context—no need for ad‑hoc scratch files or transient Redis keys. |
| **Filesystem abstraction**  | Built on `fsspec` with optional drivers for S3, Azure Blob, GCS, ABFS, SFTP, SMB, and more.     |
| **Real‑time updates**       | Server‑Sent Events (SSE) stream context changes to connected agents instantly.                  |
| **House‑keeping scheduler** | Pluggable cron jobs automatically prune expired keys and refresh embeddings.                    |
| **Container‑ready**         | Deterministic builds via `uv` lockfile; the slim Docker image is <90 MB.                        |

---

## 🚀 Quick Start

### 1. Local dev environment

```bash
git clone https://github.com/your‑org/mcp-blackboard.git
cd mcp-blackboard

# Create an isolated env & install locked deps
uv venv
uv sync

# Copy the sample env and fill in credentials
cp samples/env-sample.txt .env

# Run the server (FastAPI)
uv run src/main.py
```

The API listens on **`http://127.0.0.1:8000`** by default (see `src/server.py`).

### 2. Docker Compose

```bash
docker compose up -d
```

Compose starts:

- **mcp-blackboard** – FastAPI+SSE service
- **redis** – in‑memory store for keys, scores, embeddings

---

## ⚙️ Configuration

All settings are environment‑driven:

| Variable                                          | Purpose                            |
| ------------------------------------------------- | ---------------------------------- |
| `OPENAI_API_KEY`                                  | Embeddings / LLM calls (optional)  |
| `MCP_TRANSPORT`                                   | Event transport (`sse` or `poll`)  |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`            | Redis connection                   |
| `AZURE_STORAGE_ACCOUNT` / `AWS_ACCESS_KEY_ID` / … | Credentials for remote filesystems |

_(see `samples/env-sample.txt` for the full list)_

---

## 🏗️ Project Layout

```
.
├── src/
│   ├── common.py       # Config loader & helpers
│   ├── models.py       # Pydantic data models
│   ├── server.py       # FastAPI + APScheduler
│   └── tools.py        # Context ingestion utilities
├── samples/            # Env template & demo assets
├── tests/              # pytest suite
├── Dockerfile          # Production image
└── docker-compose.yml  # Local stack
```

---

## 🧪 Testing

```bash
pytest -q
```

---

## 🤝 Contributing

1. Fork and create a feature branch
2. Use conventional commits (`feat:`, `fix:`…)
3. Run `make lint test` locally
4. Open a PR—squash merge once approved

---

## 📜 License

Distributed under the **MIT License** – see [`LICENSE`](LICENSE) for details.

© 2025 Kwesi Apponsah
