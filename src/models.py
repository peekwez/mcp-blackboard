# type: ignore
from enum import Enum
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings


class AgentName(str, Enum):
    RESEARCHER = "researcher"
    EXTRACTOR = "extractor"
    ANALYZER = "analyzer"
    WRITER = "writer"
    EDITOR = "editor"
    EVALUATOR = "evaluator"
    PLANNER = "planner"
    CONTEXT_BUILDER = "context builder"
    VALIDATOR = "validator"
    SUMMARIZER = "summarizer"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            value_lower = value.lower()
            for member in cls:
                if member.value == value_lower:
                    return member
        return None


class StorageConfig(BaseModel):
    abfs: dict[str, str | bool | int | None] | None = None
    s3: dict[str, str | bool | int | None] | None = None
    gcs: dict[str, str | bool | int | None] | None = None
    sftp: dict[str, str | bool | int | None] | None = None
    smb: dict[str, str | bool | int | None] | None = None


class ConverterConfig(BaseModel):
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


class AppConfig(BaseSettings):
    cache_path: str
    mcp_transport: Literal["stdio", "sse"]
    redis: RedisConfig
    storage: StorageConfig
    converter: ConverterConfig


class ConverterParams(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    enable_plugins: bool = False
    llm_client: OpenAI | None = None
    llm_model: str | None = None
    docintel_endpoint: str | None = None


class PlanStep(BaseModel):
    id: int = Field(..., description="Unique identifier for the step.")
    agent: AgentName = Field(
        ..., description="The agent responsible for executing the step."
    )
    prompt: str = Field(..., description="The prompt to be sent to the agent.")
    revision: int = Field(..., description="The revision number of the step.")
    status: Literal["pending", "completed"] = Field(
        ..., description="The status of the step."
    )
    depends_on: list[int] = Field(
        ..., description="A list of step IDs that this step depends on."
    )


class Plan(BaseModel):
    id: str = Field(..., description="Unique identifier for the plan.")
    goal: str = Field(..., description="The goal of the plan.")
    steps: list[PlanStep] = Field(
        ...,
        description="A collection of steps to be executed by different agents.",
    )
