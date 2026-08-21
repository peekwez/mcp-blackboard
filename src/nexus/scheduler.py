# type: ignore

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from nexus.common import get_settings
from nexus.logging import get_logger
from nexus.tools.context import get_file_age, get_filesystem


# Set up the scheduler
def remove_stale_files(max_age: int = 3600) -> None:
    """
    Remove all files in the cache directory that are older than 1 hour.

    Args:
        max_age (int): The maximum age of files to keep in seconds.
            Default is 3600 seconds (1 hour).

    Returns:
        None
    """

    settings = get_settings()
    _, cache_path = settings.cache_path.split("://")
    fs = get_filesystem(settings.cache_path, settings)

    # remove all files older than 1 day
    try:
        for file_info in fs.listdir(cache_path):
            file_age = get_file_age(file_info)
            if file_age > max_age:
                fs.rm(f"{file_info['name']}")
    except Exception as e:
        get_logger(__name__).error(f"Error removing stale files: {e}")


def get_scheduler() -> BackgroundScheduler:
    """
    Get the background scheduler instance.

    Returns:
        BackgroundScheduler: The scheduler instance.
    """
    scheduler = BackgroundScheduler()
    trigger = CronTrigger(minute=0)  # every hour at the start of the hour
    scheduler.add_job(remove_stale_files, trigger)
    return scheduler
