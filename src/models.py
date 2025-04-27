from openai import OpenAI
from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings


class StorageConfig(BaseModel):
    abfs: dict | None = None
    s3: dict | None = None
    gcs: dict | None = None
    sftp: dict | None = None
    smb: dict | None = None


class ConverterConfig(BaseModel):
    azure_document_key: str | None = None
    azure_document_endpoint: str | None = None
    openai_api_key: str | None = None
    openai_api_base: str | None = None


class AppConfig(BaseSettings):
    cache_path: str
    storage: StorageConfig
    converter: ConverterConfig


class ConverterParams(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    enable_plugins: bool = False
    llm_client: OpenAI | None = None
    llm_model: str = "gpt-4o"
    docintel_endpoint: str | None = None
