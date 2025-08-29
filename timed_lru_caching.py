from collections import OrderedDict
from collections.abc import Callable, Hashable
import time
from typing import NamedTuple

# =============================================================================================

class _TimedLRUCacheItem[T](NamedTuple):
    """Holds the timed value in TimedLRUCache."""

    value: T
    time_added: float

# =============================================================================================

class TimedLRUCache[T]:
    """Class to create a LRU cache object that has time-to-live control."""

    def __init__(self, max_size: int = None, ttl: float = None):
        """Create a LRU cache object with time-to-live control.

        Args:
            max_size (int):
                The maximum items the cache should hold after which least used
                items are evicted.

                When null, the cache has limitless capacity.
            ttl (float):
                The time in seconds representing how long each item should
                live in cache after which they are considered stale and are
                evicted from cache.

                When null, the items in cache live forever unless evicted on
                basis of cache capacity limit, if any is set.
        """

        self._max_size = max_size
        self._ttl = ttl
        self._cache: OrderedDict[Hashable, _TimedLRUCacheItem[T]] = OrderedDict()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def get(self, key: Hashable) -> T | None:
        """Return value from cache under the key if any else return None."""

        ct = time.time()

        if key not in self._cache:
            return None

        item = self._cache[key]

        # check if expired
        if self._ttl and ct - item.time_added >= self._ttl:
            # remove and return None
            self._cache.pop(key)
            return None

        # move item up in the cache and return the item
        self._cache.move_to_end(key)

        return item.value

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def add(self, key: Hashable, value: T, time_added: float | None = None) -> None:
        """Add or update value in cache under the key."""

        ta = time.time() if time_added is None else time_added

        # cap reached, evict least used item
        if self._max_size and len(self._cache) == self._max_size:
            self._cache.popitem(last=False)

        # add the value, timestamp the value
        self._cache[key] = _TimedLRUCacheItem(value, ta)

        # move the new key up
        self._cache.move_to_end(key)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __len__(self) -> int:
        """Return the number of values in cache."""

        return len(self._cache)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def clear(self) -> None:
        """Remove all values from cache."""

        self._cache.clear()

# =============================================================================================

class _TimedLRUCacheInfo(NamedTuple):
    """Holds info about current state of the target timed lru cache."""

    hits: int
    misses: int
    current_size: int
    max_size: int

# =============================================================================================

class _TimedLRUCacheWrapper[**P, T]:
    """Class to create a wrapper to apply timed lru cache on a function."""

    def __init__(
        self, fn: Callable[P, tuple[T, float | None]], max_size: int = None, ttl: float = None
    ):
        """Creates a wrapper that applies a timed lru cache on the target func."""

        self._wrapped = fn
        self._timed_lru_cache = TimedLRUCache[T](max_size=max_size, ttl=ttl)
        self._hits = 0
        self._misses = 0
        self._max_size = max_size

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        """"""

        call_args = args + tuple(kwargs.items())

        res = self._timed_lru_cache.get(call_args)

        if res is None:
            self._misses += 1
            res, add_ts = self._wrapped(*args, **kwargs)
            self._timed_lru_cache.add(call_args, res, time_added=add_ts)
        else:
            self._hits += 1

        return res

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def cache_info(self) -> _TimedLRUCacheInfo:
        """Return current state of the underlying timed lru cache."""

        return _TimedLRUCacheInfo(
            self._hits, self._misses, len(self._timed_lru_cache), self._max_size
        )

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def clear(self) -> None:
        """Clear the underlying lru cache of the wrapped function."""

        self._timed_lru_cache.clear()
        self._hits = 0
        self._misses = 0

# =============================================================================================

def timed_lru_cache[**P, T](
    max_size: int = None, ttl: float = None
) -> Callable[[Callable[P, tuple[T, float | None]]], _TimedLRUCacheWrapper[P, T]]:
    """A decorator that applies a timed lru cache on the function.

    The function to wrap must return a tuple. The first value being the value
    computed by the function and second value being an optional timestamp. This
    allows for per value time-to-live (ttl) control. A good use for this would
    be to sync cached data across disk and memory.

    Args:
        max_size (int):
            The maximum number of values the cache can hold.

            When null, the cache can grow without limit.
        ttl (float):
            Time is seconds after which the values in cache are considered
            stale.

            When null, the values in cache live forever unless evicted on the
            basis of cache capacity control.
    """

    def deco(fn: Callable[P, tuple[T, float | None]]) -> _TimedLRUCacheWrapper[P, T]:
        return _TimedLRUCacheWrapper(fn, max_size=max_size, ttl=ttl)
    return deco

# =============================================================================================
