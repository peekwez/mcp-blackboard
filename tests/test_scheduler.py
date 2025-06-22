# type: ignore
from unittest.mock import MagicMock, patch

from nexus.scheduler import get_scheduler, remove_stale_files


@patch("nexus.scheduler.get_filesystem")
@patch("nexus.scheduler.get_settings")
@patch("nexus.scheduler.get_file_age")
def test_remove_stale_files(
    mock_get_file_age, mock_get_settings, mock_get_filesystem, settings
):
    """Test removing stale files from cache directory."""
    # Setup
    mock_get_settings.return_value = settings
    mock_fs = MagicMock()
    mock_get_filesystem.return_value = mock_fs

    # Set up file info
    file_info_recent = {"name": "recent_file.txt"}
    file_info_old = {"name": "old_file.txt"}
    mock_fs.listdir.return_value = [file_info_recent, file_info_old]

    # Mock file ages
    def file_age_side_effect(file):
        return 1800 if file == file_info_recent else 7200  # 30m and 2h

    mock_get_file_age.side_effect = file_age_side_effect

    # Execute
    remove_stale_files(3600)  # 1 hour max age

    # Assert
    mock_fs.listdir.assert_called_once()
    assert mock_get_file_age.call_count == 2
    # Only older file should be removed
    mock_fs.rm.assert_called_once_with("old_file.txt")


@patch("nexus.scheduler.get_filesystem")
@patch("nexus.scheduler.get_settings")
def test_remove_stale_files_exception(mock_get_settings, mock_get_filesystem, settings):
    """Test handling exceptions when removing stale files."""
    # Setup
    mock_get_settings.return_value = settings
    mock_fs = MagicMock()
    mock_get_filesystem.return_value = mock_fs
    mock_fs.listdir.side_effect = Exception("Test exception")

    # Execute (should not raise exception)
    remove_stale_files()

    # Assert
    mock_fs.listdir.assert_called_once()
    mock_fs.rm.assert_not_called()


def test_get_scheduler():
    """Test getting a scheduler instance."""
    # Execute
    scheduler = get_scheduler()

    # Assert
    assert scheduler is not None
    assert len(scheduler.get_jobs()) == 1
    job = scheduler.get_jobs()[0]
    assert job.func == remove_stale_files

    # Fields might be ordered differently, just check it's a cron trigger
    assert "cron" in str(job.trigger)
