# type: ignore

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from common import get_app_config
from tools.context import get_file_age, get_filesystem


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

    app_config = get_app_config()
    _, cache_path = app_config.cache_path.split("://")
    fs = get_filesystem(app_config.cache_path, app_config)

    # remove all files older than 1 day
    try:
        for file_info in fs.listdir(cache_path):
            file_age = get_file_age(file_info)
            if file_age > max_age:
                fs.rm(f"{file_info['name']}")
    except Exception as e:
        print(f"Error removing stale files: {e}")


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
    # scheduler = BackgroundScheduler()
    # trigger = CronTrigger(minute=0)  # every hour at the start of the hour
    # scheduler.add_job(remove_stale_files, trigger)
    # #scheduler.start()


# @asynccontextmanager
# async def lifespan(mcp: FastMCP):
#     yield
#     scheduler.shutdown()
