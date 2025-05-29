# type: ignore
import pytest
from pydantic import ValidationError

from models import (
    AppConfig,
    ConverterConfig,
    ConverterParams,
    Plan,
    PlanStep,
    RedisConfig,
    StorageConfig,
)


class TestRedisConfig:
    """Test the RedisConfig model."""

    def test_redis_config_default_values(self):
        """Test RedisConfig with default values."""
        config = RedisConfig(host="localhost")

        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.username is None
        assert config.password is None
        assert config.ssl is False
        assert config.ssl_ca_path is None
        assert config.ssl_cert_reqs == "required"
        assert config.ssl_ca_certs is None
        assert config.ssl_certfile is None
        assert config.ssl_keyfile is None
        assert config.socket_timeout == 10
        assert config.retry_on_timeout is True
        assert config.max_connections == 20
        assert config.decode_responses is True

    def test_redis_config_custom_values(self):
        """Test RedisConfig with custom values."""
        config = RedisConfig(
            host="redis.example.com",
            port=6380,
            db=1,
            username="user",
            password="pass",
            ssl=True,
            ssl_ca_path="/path/to/ca",
            ssl_cert_reqs="none",
            ssl_ca_certs="/path/to/certs",
            ssl_certfile="/path/to/cert",
            ssl_keyfile="/path/to/key",
            socket_timeout=30,
            retry_on_timeout=False,
            max_connections=50,
            decode_responses=False,
        )

        assert config.host == "redis.example.com"
        assert config.port == 6380
        assert config.db == 1
        assert config.username == "user"
        assert config.password == "pass"
        assert config.ssl is True
        assert config.ssl_ca_path == "/path/to/ca"
        assert config.ssl_cert_reqs == "none"
        assert config.ssl_ca_certs == "/path/to/certs"
        assert config.ssl_certfile == "/path/to/cert"
        assert config.ssl_keyfile == "/path/to/key"
        assert config.socket_timeout == 30
        assert config.retry_on_timeout is False
        assert config.max_connections == 50
        assert config.decode_responses is False


class TestStorageConfig:
    """Test the StorageConfig model."""

    def test_storage_config_default_values(self):
        """Test StorageConfig with default values."""
        config = StorageConfig()

        assert config.abfs is None
        assert config.s3 is None
        assert config.gcs is None
        assert config.sftp is None
        assert config.smb is None

    def test_storage_config_with_values(self):
        """Test StorageConfig with values."""
        config = StorageConfig(
            abfs={"account_name": "test", "account_key": "key"},
            s3={"key": "aws_key", "secret": "aws_secret"},
            gcs={"token": "gcs_token"},
            sftp={"host": "sftp.example.com", "username": "user", "password": "pass"},
            smb={
                "server_name": "smb.example.com",
                "share_name": "share",
                "username": "user",
                "password": "pass",
            },
        )

        assert config.abfs == {"account_name": "test", "account_key": "key"}
        assert config.s3 == {"key": "aws_key", "secret": "aws_secret"}
        assert config.gcs == {"token": "gcs_token"}
        assert config.sftp == {
            "host": "sftp.example.com",
            "username": "user",
            "password": "pass",
        }
        assert config.smb == {
            "server_name": "smb.example.com",
            "share_name": "share",
            "username": "user",
            "password": "pass",
        }


class TestConverterConfig:
    """Test the ConverterConfig model."""

    def test_converter_config_default_values(self):
        """Test ConverterConfig with default values."""
        config = ConverterConfig()

        assert config.azure_document_key is None
        assert config.azure_document_endpoint is None
        assert config.openai_api_key is None
        assert config.openai_api_base is None
        assert config.openai_default_model == "gpt-4o"

    def test_converter_config_custom_values(self):
        """Test ConverterConfig with custom values."""
        config = ConverterConfig(
            azure_document_key="doc_key",
            azure_document_endpoint="https://doc.example.com",
            openai_api_key="openai_key",
            openai_api_base="https://api.example.com",
            openai_default_model="gpt-3.5-turbo",
        )

        assert config.azure_document_key == "doc_key"
        assert config.azure_document_endpoint == "https://doc.example.com"
        assert config.openai_api_key == "openai_key"
        assert config.openai_api_base == "https://api.example.com"
        assert config.openai_default_model == "gpt-3.5-turbo"


class TestAppConfig:
    """Test the AppConfig model."""

    def test_app_config_creation(self):
        """Test AppConfig creation with valid data."""
        config = AppConfig(
            cache_path="file:///tmp/cache",
            mcp_transport="stdio",
            redis=RedisConfig(host="localhost"),
            storage=StorageConfig(),
            converter=ConverterConfig(),
        )

        assert config.cache_path == "file:///tmp/cache"
        assert config.mcp_transport == "stdio"
        assert isinstance(config.redis, RedisConfig)
        assert isinstance(config.storage, StorageConfig)
        assert isinstance(config.converter, ConverterConfig)

    def test_app_config_invalid_transport(self):
        """Test AppConfig with invalid transport."""
        with pytest.raises(ValidationError):
            AppConfig(
                cache_path="file:///tmp/cache",
                mcp_transport="invalid",  # Should be "stdio" or "sse"
                redis=RedisConfig(host="localhost"),
                storage=StorageConfig(),
                converter=ConverterConfig(),
            )


class TestConverterParams:
    """Test the ConverterParams model."""

    def test_converter_params_default_values(self):
        """Test ConverterParams with default values."""
        params = ConverterParams()

        assert params.enable_plugins is False
        assert params.llm_client is None
        assert params.llm_model == "gpt-4o"
        assert params.docintel_endpoint is None

    def test_converter_params_custom_values(self):
        """Test ConverterParams with custom values."""
        # Test without llm_client to avoid OpenAI validation issues
        params = ConverterParams(
            enable_plugins=True,
            llm_model="gpt-3.5-turbo",
            docintel_endpoint="https://doc.example.com",
        )

        assert params.enable_plugins is True
        assert params.llm_client is None  # Default value
        assert params.llm_model == "gpt-3.5-turbo"
        assert params.docintel_endpoint == "https://doc.example.com"


class TestPlanStep:
    """Test the PlanStep model."""

    def test_plan_step_creation(self):
        """Test PlanStep creation with valid data."""
        step = PlanStep(
            id=1,
            agent="researcher",
            prompt="Test prompt",
        )

        assert step.id == 1
        assert step.agent == "researcher"
        assert step.prompt == "Test prompt"
        assert step.revision == 0
        assert step.status == "pending"
        assert step.depends_on == []

    def test_plan_step_with_dependencies(self):
        """Test PlanStep with dependencies."""
        step = PlanStep(
            id=2,
            agent="extractor",
            prompt="Extract data",
            revision=1,
            status="completed",
            depends_on=[1],
        )

        assert step.id == 2
        assert step.agent == "extractor"
        assert step.prompt == "Extract data"
        assert step.revision == 1
        assert step.status == "completed"
        assert step.depends_on == [1]

    def test_plan_step_invalid_agent(self):
        """Test PlanStep with invalid agent."""
        with pytest.raises(ValidationError):
            PlanStep(
                id=1,
                agent="invalid_agent",
                prompt="Test prompt",
            )

    def test_plan_step_invalid_status(self):
        """Test PlanStep with invalid status."""
        with pytest.raises(ValidationError):
            PlanStep(
                id=1,
                agent="researcher",
                prompt="Test prompt",
                status="invalid_status",
            )


class TestPlan:
    """Test the Plan model."""

    def test_plan_creation(self):
        """Test Plan creation with valid data."""
        step = PlanStep(
            id=1,
            agent="researcher",
            prompt="Test prompt",
        )

        plan = Plan(
            id=1,
            goal="Test goal",
            steps=[step],
        )

        assert plan.id == 1
        assert plan.goal == "Test goal"
        assert len(plan.steps) == 1
        assert plan.steps[0] == step

    def test_plan_multiple_steps(self):
        """Test Plan with multiple steps."""
        steps = [
            PlanStep(id=1, agent="researcher", prompt="Research"),
            PlanStep(id=2, agent="extractor", prompt="Extract", depends_on=[1]),
            PlanStep(id=3, agent="analyzer", prompt="Analyze", depends_on=[2]),
        ]

        plan = Plan(
            id=1,
            goal="Complex analysis",
            steps=steps,
        )

        assert plan.id == 1
        assert plan.goal == "Complex analysis"
        assert len(plan.steps) == 3
        assert plan.steps[0].id == 1
        assert plan.steps[1].depends_on == [1]
        assert plan.steps[2].depends_on == [2]

    def test_plan_empty_steps(self):
        """Test Plan with empty steps."""
        plan = Plan(
            id=1,
            goal="Empty plan",
            steps=[],
        )

        assert plan.id == 1
        assert plan.goal == "Empty plan"
        assert plan.steps == []

    def test_plan_model_dump(self):
        """Test Plan model_dump method."""
        step = PlanStep(
            id=1,
            agent="researcher",
            prompt="Test prompt",
        )

        plan = Plan(
            id=1,
            goal="Test goal",
            steps=[step],
        )

        dumped = plan.model_dump(mode="json")

        assert dumped["id"] == 1
        assert dumped["goal"] == "Test goal"
        assert len(dumped["steps"]) == 1
        assert dumped["steps"][0]["id"] == 1
        assert dumped["steps"][0]["agent"] == "researcher"

    def test_plan_model_validate_json(self):
        """Test Plan model_validate_json method."""
        json_data = """
        {
            "id": 1,
            "goal": "Test goal",
            "steps": [
                {
                    "id": 1,
                    "agent": "researcher",
                    "prompt": "Test prompt"
                }
            ]
        }
        """

        plan = Plan.model_validate_json(json_data)

        assert plan.id == 1
        assert plan.goal == "Test goal"
        assert len(plan.steps) == 1
        assert plan.steps[0].id == 1
        assert plan.steps[0].agent == "researcher"
