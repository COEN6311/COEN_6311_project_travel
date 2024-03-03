import os
from celery import Celery
from celery.schedules import crontab

# 设置环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'COEN_6311_project_travel.settings')
# 实例化
app = Celery('COEN_6311_project_travel')

app.conf.broker_connection_retry_on_startup = True

app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动从Django的已注册app中发现任务
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'schedule_task': {  # 随便取名字
        'task': 'order.task.schedule_task',  # 指定需要定时的任务
        'schedule': crontab(),  # 删除就可以了 可以点进去这个方法看 都是*
    },
}

# 一个测试任务
@app.task(bind=True)
def debug_task(self):
    print(f'Request')


    # celery -A COEN_6311_project_travel  worker -l info -f logs/cerely.info -P threads
    # celery -A COEN_6311_project_travel  beat -l info -f logs/celery.log
