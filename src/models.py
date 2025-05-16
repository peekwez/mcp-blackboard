# type: ignore
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings


class StorageConfig(BaseModel):
    abfs: dict[str, str] | None = None
    s3: dict[str, str] | None = None
    gcs: dict[str, str] | None = None
    sftp: dict[str, str] | None = None
    smb: dict[str, str] | None = None


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
    llm_model: str = "gpt-4o"
    docintel_endpoint: str | None = None
