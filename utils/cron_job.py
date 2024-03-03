import datetime
import logging

logger = logging.getLogger(__name__)


def log_current_time():
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Current time")


if __name__ == "__main__":
    log_current_time()
