import logging
import time

logger = logging.getLogger(__name__)


class Cache(dict):
    """Simple in memory cache implementation."""

    class Item(object):
        def __init__(self, key, value, duration):
            self.key = key
            self.value = value
            self.duration = duration
            self.timestamp = time.time()

        def is_expired(self):
            return (self.timestamp + self.duration) < time.time()

        def __repr__(self):
            return '<CachedItem {{{key}:{value}}} expires at: {expire}>'.format(
                key=self.key,
                value=self.value,
                expire=self.timestamp + self.duration
            )

    def set(self, key, value, duration):
        """Set value in cache for the given duration in second."""
        self[key] = Cache.Item(key, value, duration)

    def get(self, key):
        """Get value from cache if it's not expired."""
        if key not in self or self[key].is_expired():
            return None
        else:
            return self[key].value
