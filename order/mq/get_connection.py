import pika

from COEN_6311_project_travel import settings

connection = pika.BlockingConnection(pika.ConnectionParameters(
    host=settings.RABBITMQ_HOST,
    port=settings.RABBITMQ_PORT,
    virtual_host=settings.RABBITMQ_VIRTUAL_HOST,
    credentials=pika.PlainCredentials(settings.RABBITMQ_USERNAME, settings.RABBITMQ_PASSWORD)
))
