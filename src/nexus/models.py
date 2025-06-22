# type: ignore
from enum import StrEnum
from typing import Any, Literal

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings


class StateUpdates(StrEnum):
    write_plan = "save-plan"
    update_status = "mark-plan-as-completed"
    describe_context = "save-context-description"
    write_result = "save-result"


class AgentName(StrEnum):
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
    OPTIMIZER = "optimizer"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            value_lower = value.lower()
            for member in cls:
                if member.value == value_lower:
                    return member
        return None

    def __str__(self):
        return self.value


class StorageSettings(BaseModel):
    abfs: dict[str, str | bool | int | None] | None = None
    s3: dict[str, str | bool | int | dict[str, Any] | None] | None = None
    gcs: dict[str, str | bool | int | None] | None = None
    sftp: dict[str, str | bool | int | None] | None = None
    smb: dict[str, str | bool | int | None] | None = None


class ConverterSettings(BaseModel):
    azure_document_endpoint: str | None = None
    openai_api_key: str | None = None
    openai_api_base: str | None = None
    openai_default_model: str = "gpt-4o"


class RedisSettings(BaseModel):
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


class WebSettings(BaseModel):
    tavily_api_key: str | None = None
    tavily_api_base: str = "https://api.tavily.com/v1"
    tavily_timeout: int = 3000  # in milliseconds
    tavily_max_results: int = 10


class Settings(BaseSettings):
    cache_path: str
    mcp_transport: Literal["stdio", "sse"]
    web: WebSettings
    redis: RedisSettings
    storage: StorageSettings
    converter: ConverterSettings


class ConverterParams(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    enable_plugins: bool = False
    llm_client: OpenAI | None = None
    llm_model: str | None = None
    docintel_endpoint: str | None = None


class ActionStream(BaseModel):
    """
    Represents a stream of state updates for a plan.
    """

    plan_id: str = Field(..., description="The ID of the plan.")
    action: StateUpdates = Field(..., description="The action performed on the plan.")
    data: str = Field(..., description="The data associated with the action.")
