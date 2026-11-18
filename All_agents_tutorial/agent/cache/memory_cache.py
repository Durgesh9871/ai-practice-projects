from copy import deepcopy
from threading import Lock
from time import monotonic
from typing import Any


class TTLMemoryCache:
    def __init__(self) -> None:
        self._items: dict[str, tuple[float, Any]] = {}
        self._lock = Lock()

        self._hit = 0
        self._miss = 0
        self._write = 0
    

    def remove_expired_items(self) -> None:
        with self._lock:
            current_time = monotonic()
            keys_to_remove = [
                key for key, (expires_at, _) in self._items.items()
                if current_time >= expires_at
            ]
            for key in keys_to_remove:
                del self._items[key]



    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._items.get(key)

            if item is None:
                self._miss += 1
                return None

            expires_at, value = item

            if monotonic() >= expires_at:
                del self._items[key]
                self._miss += 1
                return None

            self._hit += 1
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
            self._write += 1

    
    def clear(self, prefix: str | None = None) -> None:
        with self._lock:
            if prefix is None:
                self._items.clear()
            else:
                keys_to_remove = [key for key in self._items.keys() if key.startswith(prefix)]
                for key in keys_to_remove:
                    del self._items[key]


    
    def get_stats(self) -> dict[str, int]:
        self.remove_expired_items()
        total = self._hit + self._miss 
         
        return {
            "hit": self._hit,
            "miss": self._miss,
            "write": self._write,
            "size": len(self._items),
            "total": total,
            "hit_rate": self._hit / total if total > 0 else 0.0,
            "miss_rate": self._miss / total if total > 0 else 0.0,
        }
       

sql_result_cache = TTLMemoryCache()