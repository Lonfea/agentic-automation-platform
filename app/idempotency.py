import hashlib
import json

from redis import Redis


def payload_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


class IdempotencyStore:
    def __init__(self, redis: Redis, ttl_seconds: int = 86_400):
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    def claim(self, key: str, payload: dict) -> tuple[bool, str]:
        digest = payload_hash(payload)
        redis_key = f"idempotency:{key}"
        created = self.redis.set(redis_key, digest, nx=True, ex=self.ttl_seconds)
        if created:
            return True, digest

        existing = self.redis.get(redis_key)
        if isinstance(existing, bytes):
            existing = existing.decode()
        if existing != digest:
            raise ValueError("Idempotency key reused with a different payload.")
        return False, digest
