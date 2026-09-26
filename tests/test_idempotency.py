import pytest

from app.idempotency import IdempotencyStore


class FakeRedis:
    def __init__(self):
        self.data = {}

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.data:
            return False
        self.data[key] = value
        return True

    def get(self, key):
        return self.data.get(key)


def test_duplicate_payload_is_safe():
    store = IdempotencyStore(FakeRedis())
    first, digest = store.claim("abc", {"x": 1})
    second, duplicate_digest = store.claim("abc", {"x": 1})
    assert first is True
    assert second is False
    assert digest == duplicate_digest


def test_same_key_different_payload_is_rejected():
    store = IdempotencyStore(FakeRedis())
    store.claim("abc", {"x": 1})
    with pytest.raises(ValueError):
        store.claim("abc", {"x": 2})
