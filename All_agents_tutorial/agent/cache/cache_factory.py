from agent.cache.memory_cache import TTLMemoryCache
from agent.cache.redis_cache import RedisTTLCache
from agent.config import setting


def create_sql_result_cache():
    if setting.cache_backend == "redis":
        return RedisTTLCache(
            redis_url=setting.redis_url,
            namespace=setting.cache_namespace,
        )

    return TTLMemoryCache()


sql_result_cache = create_sql_result_cache()