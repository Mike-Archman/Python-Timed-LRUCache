# Python Timed LRU Cache

This implements a lru cache system that has time-to-live control option which in turn can be controlled at per value level.

Example Usage:
```py
from timed_lru_caching import timed_lru_cache

THE_SET_TTL = 10 * 60 # seconds

def fetch_from_cache(*args, **kwargs):
    data, save_ts = criterion_to_get_cached_data()
    if time.time() - save_ts < THE_SET_TTL:
        return cached_data, save_ts
    else:
        ...
        return None

def save_to_cache(data, save_ts):
    ...

@timed_lru_cache(max_size=5, ttl=THE_SET_TTL)
def fetch_from_api(*args, **kwargs):
    from_cache = fetch_from_cache(...)
    if not from_cache:
        data = requests.get(...).json()
        save_ts = time.time()
        save_to_cache(data, save_ts)
    else:
        data, save_ts = from_cache
    return data, save_ts
```

So this could be used in cases where the caching is to be maintained across program runs.
