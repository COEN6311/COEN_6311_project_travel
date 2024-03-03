
from celery import  shared_task
import logging


logger = logging.getLogger(__name__)


@shared_task
def test():
    print("123")
    return 1


@shared_task
def schedule_task():
    logger.info("定时任务执行了")
    print('定时任务执行了,因为在celery指定了这个名字的任务加入定时任务')
