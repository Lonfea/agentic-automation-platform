import os

from celery import Celery
from celery.exceptions import MaxRetriesExceededError

celery_app = Celery(
    "automation",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
)
celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_queue="automation",
    task_routes={"app.tasks.dead_letter": {"queue": "dead-letter"}},
)


@celery_app.task(name="app.tasks.dead_letter")
def dead_letter(event: dict, reason: str) -> dict:
    return {"status": "dead_letter", "event": event, "reason": reason}


@celery_app.task(
    bind=True,
    autoretry_for=(),
    max_retries=5,
    name="app.tasks.process_event",
)
def process_event(self, event: dict) -> dict:
    try:
        if event.get("simulate_transient_failure"):
            raise ConnectionError("Simulated transient dependency failure.")
        return {"status": "processed", "event_id": event["event_id"]}
    except (ConnectionError, TimeoutError) as exc:
        try:
            raise self.retry(
                exc=exc,
                countdown=min(300, 2 ** self.request.retries),
            )
        except MaxRetriesExceededError:
            dead_letter.apply_async(args=[event, str(exc)])
            return {"status": "dead_lettered"}
