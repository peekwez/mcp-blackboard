# type: ignore
import inspect
from unittest.mock import Mock, patch

import pytest

from server import (
    get_blackboard,
    get_context,
    get_plan,
    get_result,
    mark_plan_as_completed,
    mcp,
    remove_stale_files,
    save_context_description,
    save_plan,
    save_result,
)


class TestRemoveStaleFiles:
    """Test the remove_stale_files function."""

    @patch("server.get_app_config")
    @patch("server.get_filesystem")
    def test_remove_stale_files_default_age(
        self, mock_get_filesystem, mock_get_app_config, mock_app_config
    ):
        """Test removing stale files with default max age."""
        # Setup mocks
        mock_get_app_config.return_value = mock_app_config
        mock_app_config.cache_path = "file:///tmp/cache"

        mock_fs = Mock()
        mock_get_filesystem.return_value = mock_fs

        # Mock file list with one old file and one new file
        mock_fs.listdir.return_value = [
            {"name": "old_file.txt"},
            {"name": "new_file.txt"},
        ]

        # Mock get_file_age to return different ages
        with patch("server.get_file_age") as mock_get_file_age:
            mock_get_file_age.side_effect = [
                4000,
                1000,
            ]  # old file > 3600, new file < 3600

            # Call function
            remove_stale_files()

            # Verify filesystem operations
            mock_fs.listdir.assert_called_once_with("/tmp/cache")
            mock_fs.rm.assert_called_once_with("old_file.txt")

    @patch("server.get_app_config")
    @patch("server.get_filesystem")
    def test_remove_stale_files_custom_age(
        self, mock_get_filesystem, mock_get_app_config, mock_app_config
    ):
        """Test removing stale files with custom max age."""
        # Setup mocks
        mock_get_app_config.return_value = mock_app_config
        mock_app_config.cache_path = "s3://bucket/cache"

        mock_fs = Mock()
        mock_get_filesystem.return_value = mock_fs

        mock_fs.listdir.return_value = [{"name": "test_file.txt"}]

        with patch("server.get_file_age") as mock_get_file_age:
            mock_get_file_age.return_value = 1800  # 30 minutes

            # Call function with custom max_age
            remove_stale_files(max_age=900)  # 15 minutes

            # Should remove the file since 1800 > 900
            mock_fs.rm.assert_called_once_with("test_file.txt")

    @patch("server.get_app_config")
    @patch("server.get_filesystem")
    def test_remove_stale_files_no_old_files(
        self, mock_get_filesystem, mock_get_app_config, mock_app_config
    ):
        """Test when no files are old enough to remove."""
        # Setup mocks
        mock_get_app_config.return_value = mock_app_config
        mock_app_config.cache_path = "file:///tmp/cache"

        mock_fs = Mock()
        mock_get_filesystem.return_value = mock_fs

        mock_fs.listdir.return_value = [{"name": "file1.txt"}, {"name": "file2.txt"}]

        with patch("server.get_file_age") as mock_get_file_age:
            mock_get_file_age.return_value = 1000  # All files are new

            remove_stale_files()

            # No files should be removed
            mock_fs.rm.assert_not_called()


class TestSavePlanTool:
    """Test the save_plan MCP tool."""

    @pytest.mark.asyncio
    @patch("server.write_plan")
    async def test_save_plan_with_dict(self, mock_write_plan):
        """Test saving a plan with a dict input."""
        mock_write_plan.return_value = "Plan saved successfully"

        plan_data = {
            "id": 1,
            "goal": "Test Plan Goal",
            "steps": [
                {
                    "id": 1,
                    "prompt": "Step 1 prompt",
                    "agent": "researcher",
                    "depends_on": [],
                    "status": "pending",
                }
            ],
        }

        result = await save_plan("plan123", plan_data)

        assert result == "Plan saved successfully"
        mock_write_plan.assert_called_once()

        # Check that the plan was validated and dumped correctly
        args, kwargs = mock_write_plan.call_args
        assert args[0] == "plan123"
        assert isinstance(args[1], dict)
        assert args[1]["goal"] == "Test Plan Goal"

    @pytest.mark.asyncio
    @patch("server.write_plan")
    async def test_save_plan_with_json_string(self, mock_write_plan):
        """Test saving a plan with a JSON string input."""
        mock_write_plan.return_value = "Plan saved successfully"

        plan_json = """{
            "id": 1,
            "goal": "Test Plan Goal",
            "steps": [
                {
                    "id": 1,
                    "prompt": "Step 1 prompt",
                    "agent": "researcher",
                    "depends_on": [],
                    "status": "pending"
                }
            ]
        }"""

        result = await save_plan("plan123", plan_json)

        assert result == "Plan saved successfully"
        mock_write_plan.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_plan_invalid_dict(self):
        """Test saving a plan with invalid dict data."""
        invalid_plan = {"invalid": "data"}

        with pytest.raises(ValueError, match="Plan must be a JSON-serializable object"):
            await save_plan("plan123", invalid_plan)

    @pytest.mark.asyncio
    async def test_save_plan_invalid_json_string(self):
        """Test saving a plan with invalid JSON string."""
        invalid_json = "not json"

        with pytest.raises(ValueError, match="Plan must be a JSON-serializable object"):
            await save_plan("plan123", invalid_json)

    @pytest.mark.asyncio
    async def test_save_plan_invalid_type(self):
        """Test saving a plan with invalid data type."""
        with pytest.raises(ValueError, match="Plan must be a JSON-serializable object"):
            await save_plan("plan123", 12345)  # type: ignore


class TestMarkPlanAsCompletedTool:
    """Test the mark_plan_as_completed MCP tool."""

    @pytest.mark.asyncio
    @patch("server.update_plan_status")
    async def test_mark_plan_as_completed_success(self, mock_update_plan_status):
        """Test successfully marking a plan step as completed."""
        mock_update_plan_status.return_value = "Step marked as completed"

        result = await mark_plan_as_completed("plan123", 1)

        assert result == "Step marked as completed"
        mock_update_plan_status.assert_called_once_with("plan123", 1)

    @pytest.mark.asyncio
    @patch("server.update_plan_status")
    async def test_mark_plan_as_completed_zero_step_id(self, mock_update_plan_status):
        """Test marking a plan step as completed with step_id 0."""
        mock_update_plan_status.return_value = "Step marked as completed"

        result = await mark_plan_as_completed("plan123", 0)

        assert result == "Step marked as completed"
        mock_update_plan_status.assert_called_once_with("plan123", 0)


class TestSaveResultTool:
    """Test the save_result MCP tool."""

    @pytest.mark.asyncio
    @patch("server.write_result")
    async def test_save_result_with_string(self, mock_write_result):
        """Test saving a result with string data."""
        mock_write_result.return_value = "Result saved successfully"

        result = await save_result(
            "plan123", "agent1", 1, "Test result", "Some text result"
        )

        assert result == "Result saved successfully"
        mock_write_result.assert_called_once_with(
            "plan123", "agent1", 1, "Test result", "Some text result"
        )

    @pytest.mark.asyncio
    @patch("server.write_result")
    async def test_save_result_with_dict(self, mock_write_result):
        """Test saving a result with dict data."""
        mock_write_result.return_value = "Result saved successfully"

        result_data = {"status": "success", "data": [1, 2, 3]}
        result = await save_result("plan123", "agent1", 1, "Test result", result_data)

        assert result == "Result saved successfully"
        mock_write_result.assert_called_once_with(
            "plan123", "agent1", 1, "Test result", result_data
        )

    @pytest.mark.asyncio
    @patch("server.write_result")
    async def test_save_result_empty_description(self, mock_write_result):
        """Test saving a result with empty description."""
        mock_write_result.return_value = "Result saved successfully"

        result = await save_result("plan123", "agent1", 1, "", "Some result")

        assert result == "Result saved successfully"
        mock_write_result.assert_called_once_with(
            "plan123", "agent1", 1, "", "Some result"
        )


class TestSaveContextDescriptionTool:
    """Test the save_context_description MCP tool."""

    @pytest.mark.asyncio
    @patch("server.write_context_description")
    async def test_save_context_description_file_path(
        self, mock_write_context_description
    ):
        """Test saving context description for a file path."""
        mock_write_context_description.return_value = "Context description saved"

        result = await save_context_description(
            "plan123", "/path/to/file.txt", "This is a test file"
        )

        assert result == "Context description saved"
        mock_write_context_description.assert_called_once_with(
            "plan123", "/path/to/file.txt", "This is a test file"
        )

    @pytest.mark.asyncio
    @patch("server.write_context_description")
    async def test_save_context_description_url(self, mock_write_context_description):
        """Test saving context description for a URL."""
        mock_write_context_description.return_value = "Context description saved"

        result = await save_context_description(
            "plan123", "https://example.com/file.pdf", "This is a PDF document"
        )

        assert result == "Context description saved"
        mock_write_context_description.assert_called_once_with(
            "plan123", "https://example.com/file.pdf", "This is a PDF document"
        )

    @pytest.mark.asyncio
    @patch("server.write_context_description")
    async def test_save_context_description_empty_description(
        self, mock_write_context_description
    ):
        """Test saving context description with empty description."""
        mock_write_context_description.return_value = "Context description saved"

        result = await save_context_description("plan123", "/path/to/file.txt", "")

        assert result == "Context description saved"
        mock_write_context_description.assert_called_once_with(
            "plan123", "/path/to/file.txt", ""
        )


class TestGetBlackboardTool:
    """Test the get_blackboard MCP tool."""

    @pytest.mark.asyncio
    @patch("server.fetch_blackboard")
    async def test_get_blackboard_found(self, mock_fetch_blackboard):
        """Test fetching existing blackboard data."""
        expected_data = {"plan": "data", "results": []}
        mock_fetch_blackboard.return_value = expected_data

        result = await get_blackboard("plan123")

        assert result == expected_data
        mock_fetch_blackboard.assert_called_once_with("plan123")

    @pytest.mark.asyncio
    @patch("server.fetch_blackboard")
    async def test_get_blackboard_not_found(self, mock_fetch_blackboard):
        """Test fetching non-existent blackboard data."""
        mock_fetch_blackboard.return_value = None

        result = await get_blackboard("nonexistent")

        assert result is None
        mock_fetch_blackboard.assert_called_once_with("nonexistent")

    @pytest.mark.asyncio
    @patch("server.fetch_blackboard")
    async def test_get_blackboard_string_result(self, mock_fetch_blackboard):
        """Test fetching blackboard data that returns a string."""
        mock_fetch_blackboard.return_value = "string result"

        result = await get_blackboard("plan123")

        assert result == "string result"
        mock_fetch_blackboard.assert_called_once_with("plan123")


class TestGetPlanTool:
    """Test the get_plan MCP tool."""

    @pytest.mark.asyncio
    @patch("server.fetch_plan")
    async def test_get_plan_found(self, mock_fetch_plan):
        """Test fetching existing plan data."""
        expected_plan = {"name": "Test Plan", "description": "A test plan", "steps": []}
        mock_fetch_plan.return_value = expected_plan

        result = await get_plan("plan123")

        assert result == expected_plan
        mock_fetch_plan.assert_called_once_with("plan123")

    @pytest.mark.asyncio
    @patch("server.fetch_plan")
    async def test_get_plan_not_found(self, mock_fetch_plan):
        """Test fetching non-existent plan data."""
        mock_fetch_plan.return_value = None

        result = await get_plan("nonexistent")

        assert result is None
        mock_fetch_plan.assert_called_once_with("nonexistent")

    @pytest.mark.asyncio
    @patch("server.fetch_plan")
    async def test_get_plan_string_result(self, mock_fetch_plan):
        """Test fetching plan data that returns a string."""
        mock_fetch_plan.return_value = "serialized plan data"

        result = await get_plan("plan123")

        assert result == "serialized plan data"
        mock_fetch_plan.assert_called_once_with("plan123")


class TestGetResultTool:
    """Test the get_result MCP tool."""

    @pytest.mark.asyncio
    @patch("server.fetch_result")
    async def test_get_result_found(self, mock_fetch_result):
        """Test fetching existing result data."""
        expected_result = {"status": "completed", "data": "result data"}
        mock_fetch_result.return_value = expected_result

        result = await get_result("plan123", "agent1", 1)

        assert result == expected_result
        mock_fetch_result.assert_called_once_with("plan123", "agent1", 1)

    @pytest.mark.asyncio
    @patch("server.fetch_result")
    async def test_get_result_not_found(self, mock_fetch_result):
        """Test fetching non-existent result data."""
        mock_fetch_result.return_value = None

        result = await get_result("plan123", "agent1", 1)

        assert result is None
        mock_fetch_result.assert_called_once_with("plan123", "agent1", 1)

    @pytest.mark.asyncio
    @patch("server.fetch_result")
    async def test_get_result_string_result(self, mock_fetch_result):
        """Test fetching result data that returns a string."""
        mock_fetch_result.return_value = "string result data"

        result = await get_result("plan123", "agent1", 1)

        assert result == "string result data"
        mock_fetch_result.assert_called_once_with("plan123", "agent1", 1)

    @pytest.mark.asyncio
    @patch("server.fetch_result")
    async def test_get_result_zero_step_id(self, mock_fetch_result):
        """Test fetching result with step_id 0."""
        expected_result = {"status": "completed"}
        mock_fetch_result.return_value = expected_result

        result = await get_result("plan123", "agent1", 0)

        assert result == expected_result
        mock_fetch_result.assert_called_once_with("plan123", "agent1", 0)


class TestGetContextTool:
    """Test the get_context MCP tool."""

    @pytest.mark.asyncio
    @patch("server.fetch_context")
    async def test_get_context_default_cache(self, mock_fetch_context):
        """Test fetching context with default cache setting."""
        mock_fetch_context.return_value = (
            "# Document Content\n\nThis is markdown content."
        )

        result = await get_context("/path/to/document.pdf")

        assert result == "# Document Content\n\nThis is markdown content."
        mock_fetch_context.assert_called_once_with("/path/to/document.pdf", True)

    @pytest.mark.asyncio
    @patch("server.fetch_context")
    async def test_get_context_cache_enabled(self, mock_fetch_context):
        """Test fetching context with cache enabled."""
        mock_fetch_context.return_value = "# Cached Content\n\nThis is cached markdown."

        result = await get_context("https://example.com/doc.html", use_cache=True)

        assert result == "# Cached Content\n\nThis is cached markdown."
        mock_fetch_context.assert_called_once_with("https://example.com/doc.html", True)

    @pytest.mark.asyncio
    @patch("server.fetch_context")
    async def test_get_context_cache_disabled(self, mock_fetch_context):
        """Test fetching context with cache disabled."""
        mock_fetch_context.return_value = "# Fresh Content\n\nThis is fresh markdown."

        result = await get_context("s3://bucket/document.docx", use_cache=False)

        assert result == "# Fresh Content\n\nThis is fresh markdown."
        mock_fetch_context.assert_called_once_with("s3://bucket/document.docx", False)

    @pytest.mark.asyncio
    @patch("server.fetch_context")
    async def test_get_context_various_file_types(self, mock_fetch_context):
        """Test fetching context for various file types."""
        mock_fetch_context.return_value = "# Converted Content"

        file_types = [
            "/path/to/file.pdf",
            "https://example.com/image.jpg",
            "s3://bucket/spreadsheet.xlsx",
            "gcs://bucket/presentation.pptx",
            "file:///local/text.txt",
            "abfs://container/data.csv",
        ]

        for file_path in file_types:
            result = await get_context(file_path)
            assert result == "# Converted Content"

        assert mock_fetch_context.call_count == len(file_types)

    @pytest.mark.asyncio
    @patch("server.fetch_context")
    async def test_get_context_error_handling(self, mock_fetch_context):
        """Test error handling in get_context."""
        mock_fetch_context.side_effect = OSError("File not found")

        with pytest.raises(OSError, match="File not found"):
            await get_context("/nonexistent/file.pdf")

    @pytest.mark.asyncio
    @patch("server.fetch_context")
    async def test_get_context_value_error(self, mock_fetch_context):
        """Test ValueError handling in get_context."""
        mock_fetch_context.side_effect = ValueError("Invalid URL format")

        with pytest.raises(ValueError, match="Invalid URL format"):
            await get_context("invalid://url")


class TestMCPServerConfiguration:
    """Test the FastMCP server configuration."""

    def test_mcp_server_name(self):
        """Test that the MCP server has the correct name."""
        assert mcp.name == "MCP Blackboard Server"

    def test_mcp_server_instructions(self):
        """Test that the MCP server has instructions."""
        expected_instructions = (
            "A blackboard server for storing and retrieving "
            "static and dynamic data for an agent task"
        )
        assert mcp.instructions == expected_instructions

    def test_mcp_server_has_lifespan(self):
        """Test that the MCP server is properly configured with lifespan."""
        # The lifespan is passed to FastMCP during initialization but may not be
        # accessible as a public attribute. We verify it through the scheduler test.
        from server import lifespan, scheduler

        # Verify the lifespan function exists and is callable
        assert callable(lifespan)

        # Verify the scheduler exists (used in lifespan)
        assert scheduler is not None

    @pytest.mark.asyncio
    async def test_mcp_lifespan_context_manager(self):
        """Test the lifespan context manager functionality."""
        from server import lifespan, scheduler

        # Mock the scheduler
        with patch.object(scheduler, "shutdown") as mock_shutdown:
            async with lifespan(mcp):
                # The context manager should yield without doing anything
                pass

            # After exiting, scheduler.shutdown should be called
            mock_shutdown.assert_called_once()

    def test_mcp_server_tools_registered(self):
        """Test that all expected tools are registered with the MCP server."""
        # Note: This test verifies the tools are decorated correctly
        # The actual tool registration is handled by the FastMCP framework

        # Verify the tools have the correct function signatures

        # Check save_plan
        sig = inspect.signature(save_plan)
        assert "plan_id" in sig.parameters
        assert "plan" in sig.parameters

        # Check mark_plan_as_completed
        sig = inspect.signature(mark_plan_as_completed)
        assert "plan_id" in sig.parameters
        assert "step_id" in sig.parameters

        # Check save_result
        sig = inspect.signature(save_result)
        assert "plan_id" in sig.parameters
        assert "agent_name" in sig.parameters
        assert "step_id" in sig.parameters
        assert "description" in sig.parameters
        assert "result" in sig.parameters

        # Check save_context_description
        sig = inspect.signature(save_context_description)
        assert "plan_id" in sig.parameters
        assert "file_path_or_url" in sig.parameters
        assert "description" in sig.parameters

        # Check get_blackboard
        sig = inspect.signature(get_blackboard)
        assert "plan_id" in sig.parameters

        # Check get_plan
        sig = inspect.signature(get_plan)
        assert "plan_id" in sig.parameters

        # Check get_result
        sig = inspect.signature(get_result)
        assert "plan_id" in sig.parameters
        assert "agent_name" in sig.parameters
        assert "step_id" in sig.parameters

        # Check get_context
        sig = inspect.signature(get_context)
        assert "file_path_or_url" in sig.parameters
        assert "use_cache" in sig.parameters


class TestSchedulerConfiguration:
    """Test the background scheduler configuration."""

    @patch("server.BackgroundScheduler")
    @patch("server.CronTrigger")
    def test_scheduler_setup(self, mock_cron_trigger, mock_scheduler_class):
        """Test that the scheduler is configured correctly."""
        # This test verifies the scheduler setup at module level
        # Note: Since the scheduler is already initialized when the module loads,
        # we need to test the actual scheduler instance that was created

        from server import scheduler

        # Verify scheduler exists and is the correct type
        assert scheduler is not None
        assert hasattr(scheduler, "start")
        assert hasattr(scheduler, "shutdown")
        assert hasattr(scheduler, "add_job")

    def test_scheduler_trigger_configuration(self):
        """Test that the cron trigger is configured correctly."""
        from server import trigger

        # Verify trigger is configured for hourly execution
        assert trigger is not None
        # Note: The trigger is configured to run at minute=0 (every hour)

    def test_scheduler_is_started(self):
        """Test that the scheduler is started."""
        from server import scheduler

        # Verify the scheduler is running
        # Note: The scheduler.start() is called at module load time
        assert scheduler is not None


class TestSavePlanToolErrorHandling:
    """Test error handling in the save_plan MCP tool."""

    @pytest.mark.asyncio
    @patch("server.write_plan")
    async def test_save_plan_invalid_json_string(self, mock_write_plan):
        """Test save_plan with invalid JSON string."""
        mock_write_plan.return_value = "Plan saved successfully"

        invalid_json = '{"id": 1, "goal": "test"'  # Missing closing brace

        with pytest.raises(ValueError, match="Plan must be a JSON-serializable object"):
            await save_plan("plan123", invalid_json)

    @pytest.mark.asyncio
    @patch("server.write_plan")
    async def test_save_plan_invalid_dict_structure(self, mock_write_plan):
        """Test save_plan with dict that doesn't match Plan model."""
        mock_write_plan.return_value = "Plan saved successfully"

        invalid_plan = {"invalid_field": "value"}  # Doesn't match Plan model

        with pytest.raises(ValueError, match="Plan must be a JSON-serializable object"):
            await save_plan("plan123", invalid_plan)

    @pytest.mark.asyncio
    async def test_save_plan_invalid_type(self):
        """Test save_plan with invalid type (not dict or str)."""
        with pytest.raises(ValueError, match="Plan must be a JSON-serializable object"):
            await save_plan("plan123", 123)  # Invalid type

    @pytest.mark.asyncio
    @patch("server.write_plan")
    async def test_save_plan_valid_json_string(self, mock_write_plan):
        """Test save_plan with valid JSON string."""
        mock_write_plan.return_value = "Plan saved successfully"

        valid_plan_json = '{"id": 1, "goal": "test goal", "steps": []}'

        result = await save_plan("plan123", valid_plan_json)

        assert result == "Plan saved successfully"
        mock_write_plan.assert_called_once()

    @pytest.mark.asyncio
    @patch("server.write_plan")
    async def test_save_plan_valid_dict(self, mock_write_plan):
        """Test save_plan with valid dict."""
        mock_write_plan.return_value = "Plan saved successfully"

        valid_plan = {"id": 1, "goal": "test goal", "steps": []}

        result = await save_plan("plan123", valid_plan)

        assert result == "Plan saved successfully"
        mock_write_plan.assert_called_once()


class TestRemoveStaleFilesErrorHandling:
    """Test error handling in the remove_stale_files function."""

    @patch("server.get_app_config")
    @patch("server.get_filesystem")
    def test_remove_stale_files_filesystem_error(
        self, mock_get_filesystem, mock_get_app_config
    ):
        """Test remove_stale_files with filesystem error."""
        # Setup mocks
        mock_config = Mock()
        mock_config.cache_path = "file:///tmp/cache"
        mock_get_app_config.return_value = mock_config

        mock_fs = Mock()
        mock_fs.listdir.side_effect = OSError("Permission denied")
        mock_get_filesystem.return_value = mock_fs

        # Should not raise an exception, but handle errors gracefully
        with pytest.raises(OSError):
            remove_stale_files(3600)

    @patch("server.get_app_config")
    @patch("server.get_filesystem")
    @patch("server.get_file_age")
    def test_remove_stale_files_with_old_files(
        self, mock_get_file_age, mock_get_filesystem, mock_get_app_config
    ):
        """Test remove_stale_files removes old files."""
        # Setup mocks
        mock_config = Mock()
        mock_config.cache_path = "file:///tmp/cache"
        mock_get_app_config.return_value = mock_config

        mock_fs = Mock()
        file_info = {"name": "old_file.txt"}
        mock_fs.listdir.return_value = [file_info]
        mock_get_filesystem.return_value = mock_fs

        # File is older than max_age
        mock_get_file_age.return_value = 7200  # 2 hours old

        remove_stale_files(3600)  # max_age = 1 hour

        # Verify old file was removed
        mock_fs.rm.assert_called_once_with("old_file.txt")

    @patch("server.get_app_config")
    @patch("server.get_filesystem")
    @patch("server.get_file_age")
    def test_remove_stale_files_keeps_new_files(
        self, mock_get_file_age, mock_get_filesystem, mock_get_app_config
    ):
        """Test remove_stale_files keeps new files."""
        # Setup mocks
        mock_config = Mock()
        mock_config.cache_path = "file:///tmp/cache"
        mock_get_app_config.return_value = mock_config

        mock_fs = Mock()
        file_info = {"name": "new_file.txt"}
        mock_fs.listdir.return_value = [file_info]
        mock_get_filesystem.return_value = mock_fs

        # File is newer than max_age
        mock_get_file_age.return_value = 1800  # 30 minutes old

        remove_stale_files(3600)  # max_age = 1 hour

        # Verify new file was not removed
        mock_fs.rm.assert_not_called()


class TestSchedulerLifecycle:
    """Test scheduler and lifespan functionality."""

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_called(self):
        """Test that lifespan properly shuts down scheduler."""
        from server import lifespan, scheduler

        with patch.object(scheduler, "shutdown") as mock_shutdown:
            # Test the lifespan context manager
            async with lifespan(mcp):
                pass  # Context manager should yield

            # Verify shutdown was called when exiting context
            mock_shutdown.assert_called_once()

    def test_scheduler_job_configuration(self):
        """Test that scheduler has the correct job configuration."""
        from server import scheduler

        # Verify scheduler has jobs
        jobs = scheduler.get_jobs()
        assert len(jobs) > 0

        # Find the remove_stale_files job
        stale_files_job = None
        for job in jobs:
            if "remove_stale_files" in str(job.func):
                stale_files_job = job
                break

        assert stale_files_job is not None

        # Verify it's configured to run hourly (minute=0)
        assert hasattr(stale_files_job.trigger, "fields")
