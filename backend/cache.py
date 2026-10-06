"""Results cache for the heavy calculations (closure, forecast, plan, drones, what-ifs, alerts)."""
import functools
import threading


def memo(maxsize: int):
    """Like functools.lru_cache, but each result is computed only once. A caller that asks for a result
    while another caller is still computing it waits for that one instead of starting a second copy.
    Without this, a few page reloads on a fresh start piled up many slow copies of the same calculation."""
    def wrap(fn):
        cached = functools.lru_cache(maxsize=maxsize)(fn)
        locks: dict = {}

        @functools.wraps(fn)
        def call(*args, **kw):
            with locks.setdefault((args, tuple(sorted(kw.items()))), threading.Lock()):
                return cached(*args, **kw)

        call.cache_clear = cached.cache_clear
        return call
    return wrap
