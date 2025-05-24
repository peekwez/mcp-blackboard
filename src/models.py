from typing import Any, Literal

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field

# from pydantic_settings import BaseSettings


class StorageConfig(BaseModel):
    abfs: dict[str, Any] | None = None
    s3: dict[str, Any] | None = None
    gcs: dict[str, Any] | None = None
    sftp: dict[str, Any] | None = None
    smb: dict[str, Any] | None = None


class ConverterConfig(BaseModel):
    azure_document_key: str | None = None
    azure_document_endpoint: str | None = None
    openai_api_key: str | None = None
    openai_api_base: str | None = None
    openai_default_model: str = "gpt-4o"


class RedisConfig(BaseModel):
    host: str
    port: int = 6379
    db: int = 0
    username: str | None = None
    password: str | None = None
    ssl: bool = False
    ssl_ca_path: str | None = None
    ssl_cert_reqs: str = "required"
    ssl_ca_certs: str | None = None
    ssl_certfile: str | None = None
    ssl_keyfile: str | None = None
    socket_timeout: int = 10
    retry_on_timeout: bool = True
    max_connections: int = 20
    decode_responses: bool = True


class AppConfig(BaseModel):
    cache_path: str
    mcp_transport: Literal["stdio", "sse"]
    redis: RedisConfig
    storage: StorageConfig
    converter: ConverterConfig


class ConverterParams(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    enable_plugins: bool = False
    llm_client: OpenAI | None = None
    llm_model: str = "gpt-4o"
    docintel_endpoint: str | None = None


class PlanStep(BaseModel):
    id: int = Field(..., description="Unique identifier for the step")
    agent: Literal[
        "researcher",
        "extractor",
        "analyzer",
        "writer",
        "editor",
        "evaluator",
    ] = Field(..., description="The agent responsible for this step")
    prompt: str = Field(..., description="The prompt or task description for the agent")
    revision: int = Field(
        0, description="Revision number for the step, incremented with each update"
    )
    status: Literal["pending", "completed", "failed"] = Field(
        "pending", description="Current status of the step"
    )
    depends_on: list[int] = Field(
        ..., description="List of step IDs that this step depends on"
    )


class Plan(BaseModel):
    id: int = Field(..., description="Unique identifier for the plan")
    goal: str = Field(..., description="The main goal or objective of the plan")
    steps: list[PlanStep] = Field(..., description="List of steps in the plan")
