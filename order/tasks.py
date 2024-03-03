from datetime import time

from celery import Celery

app = Celery('COEN_6311_project_travel')


@app.task
def test():
    print("123")
    return 1

