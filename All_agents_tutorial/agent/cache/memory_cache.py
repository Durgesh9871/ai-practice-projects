from copy import deepcopy
from threading import Lock
from time import monotonic
from typing import Any


class TTLMemoryCache:
    def __init__(self) -> None:
        self._items: dict[str, tuple[float, Any]] = {}
        self._lock = Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._items.get(key)

            if item is None:
                return None

            expires_at, value = item

            if monotonic() >= expires_at:
                del self._items[key]
                return None

            return deepcopy(value)

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int,
    ) -> None:
        with self._lock:
            self._items[key] = (
                monotonic() + ttl_seconds,
                deepcopy(value),
            )


sql_result_cache = TTLMemoryCache()