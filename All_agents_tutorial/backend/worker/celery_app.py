from celery import Celery
from agent.config import setting


celery_app = Celery(
    "self_driving_analyst",
    broker=setting.celery_broker_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    task_ignore_result=True,
    timezone="UTC",
    enable_utc=True,
)