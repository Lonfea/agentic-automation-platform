import os

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field
from redis import Redis

from app.idempotency import IdempotencyStore
from app.tasks import process_event

app = FastAPI(title="Agentic Automation Pipeline", version="0.1.0")
redis = Redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    decode_responses=True,
)
idempotency = IdempotencyStore(redis)


class WebhookEvent(BaseModel):
    event_id: str = Field(min_length=1, max_length=200)
    event_type: str = Field(min_length=1, max_length=200)
    payload: dict = Field(default_factory=dict)


@app.post("/webhooks/events", status_code=status.HTTP_202_ACCEPTED)
def webhook(
    event: WebhookEvent,
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> dict:
    body = event.model_dump()
    try:
        claimed, digest = idempotency.claim(idempotency_key, body)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if not claimed:
        return {
            "accepted": True,
            "duplicate": True,
            "idempotency_hash": digest,
        }

    task = process_event.apply_async(args=[body])
    return {
        "accepted": True,
        "duplicate": False,
        "task_id": task.id,
        "idempotency_hash": digest,
    }
