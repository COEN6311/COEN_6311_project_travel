import os
from celery import Celery
from celery.schedules import crontab

# Set the environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'COEN_6311_project_travel.settings')

# Instantiate Celery
app = Celery('COEN_6311_project_travel')

# Retry establishing the broker connection on startup
app.conf.broker_connection_retry_on_startup = True

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatically discover tasks from Django registered apps
app.autodiscover_tasks()

# Define the Celery beat schedule
app.conf.beat_schedule = {
    # Uncomment and modify the schedule below as needed
    # 'schedule_task': {
    #     'task': 'order.task.schedule_task',
    #     'schedule': crontab(),
    # },
    'change_order_status_task': {
        'task': 'order.task.change_order_status_task',
        # Run once per day at 00:01
        'schedule': crontab(hour=0, minute=1),
    },
}

# Define a test task
@app.task(bind=True)
def debug_task(self):
    print(f'Request')
