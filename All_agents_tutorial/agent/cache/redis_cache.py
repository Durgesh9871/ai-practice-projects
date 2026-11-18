import json
from typing import Any

from redis import Redis
from redis.exceptions import RedisError
from uuid import uuid4


class RedisTTLCache:
    def __init__(
        self,
        redis_url: str,
        namespace: str,
    ) -> None:
        self._client = Redis.from_url(
            redis_url,
            decode_responses=True,
        )
        self._namespace = namespace

    def _data_key(self, key: str) -> str:
        return f"{self._namespace}:data:{key}"

    def _metric_key(self, name: str) -> str:
        return f"{self._namespace}:metrics:{name}"

    def _increment_metric(self, name: str) -> None:
        try:
            self._client.incr(self._metric_key(name))
        except RedisError:
            pass

    def get(self, key: str) -> Any | None:
        try:
            raw_value = self._client.get(self._data_key(key))

            if raw_value is None:
                self._increment_metric("misses")
                return None

            self._increment_metric("hits")
            return json.loads(raw_value)

        except (RedisError, json.JSONDecodeError):
            self._increment_metric("errors")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int,
    ) -> None:
        try:
            self._client.set(
                self._data_key(key),
                json.dumps(value),
                ex=ttl_seconds,
            )
            self._increment_metric("writes")

        except (RedisError, TypeError):
            self._increment_metric("errors")

    def clear(self, prefix: str | None = None) -> int:
        try:
            key_prefix = self._data_key(prefix or "")
            keys = list(
                self._client.scan_iter(
                    match=f"{key_prefix}*"
                )
            )

            if not keys:
                return 0

            return self._client.delete(*keys)

        except RedisError:
            self._increment_metric("errors")
            return 0

    def get_stats(self) -> dict[str, int | float]:
        try:
            hits = int(
                self._client.get(
                    self._metric_key("hits")
                ) or 0
            )
            misses = int(
                self._client.get(
                    self._metric_key("misses")
                ) or 0
            )
            writes = int(
                self._client.get(
                    self._metric_key("writes")
                ) or 0
            )
            errors = int(
                self._client.get(
                    self._metric_key("errors")
                ) or 0
            )

            total = hits + misses

            return {
                "hits": hits,
                "misses": misses,
                "writes": writes,
                "errors": errors,
                "total": total,
                "hit_rate": hits / total if total else 0,
            }

        except RedisError:
            return {
                "hits": 0,
                "misses": 0,
                "writes": 0,
                "errors": 1,
                "total": 0,
                "hit_rate": 0,
            }

    def _lock_key(self, key: str) -> str:
        return f"{self._namespace}:lock:{key}"


    

    def acquire_lock(self, key: str, ttl_seconds: int) -> str | None:
        try:
            token = str(uuid4())
            acquired = self._client.set(
                self._lock_key(key),
                token,
                nx=True,
                ex=ttl_seconds,
            )
            return token if acquired else None
        except RedisError:
            return None


    def release_lock(self, key: str, token: str) -> None:
        try:
            release_lock_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            end
            return 0
            """
            self._client.eval(
                release_lock_script,
                1,
                self._lock_key(key),
                token,
            )
        except RedisError:
            pass