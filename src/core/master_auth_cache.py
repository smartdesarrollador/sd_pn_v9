"""
Master Authentication Cache
Temporary cache to avoid asking for master password on every operation
Cache is valid for a configurable duration (default: 5 minutes)
"""
import time
import logging

logger = logging.getLogger(__name__)


class MasterAuthCache:
    """
    Temporary authentication cache for master password

    Stores authentication state for a limited time to provide
    better UX when accessing multiple sensitive items.

    Cache is invalidated on:
    - Timeout expiration (default: 5 minutes)
    - Manual invalidation (e.g., logout)
    - Application close
    """

    # Cache duration in seconds (5 minutes by default)
    CACHE_DURATION = 300  # 5 minutes = 300 seconds

    def __init__(self):
        """Initialize authentication cache"""
        self._authenticated = False
        self._auth_timestamp = 0
        logger.debug("MasterAuthCache initialized")

    def authenticate(self):
        """
        Mark as authenticated

        Called after successful master password verification.
        Starts the cache timer.
        """
        self._authenticated = True
        self._auth_timestamp = time.time()
        logger.info(f"Master password cache authenticated (valid for {self.CACHE_DURATION}s)")

    def is_authenticated(self) -> bool:
        """
        Check if cache is valid

        Returns:
            True if authenticated and cache not expired, False otherwise
        """
        if not self._authenticated:
            logger.debug("Cache not authenticated")
            return False

        # Check expiration
        elapsed = time.time() - self._auth_timestamp
        if elapsed > self.CACHE_DURATION:
            logger.info(f"Cache expired after {elapsed:.1f}s (limit: {self.CACHE_DURATION}s)")
            self.invalidate()
            return False

        remaining = self.CACHE_DURATION - elapsed
        logger.debug(f"Cache valid - {remaining:.1f}s remaining")
        return True

    def invalidate(self):
        """
        Invalidate cache

        Called on:
        - Timeout expiration
        - User logout
        - Application close
        """
        was_authenticated = self._authenticated
        self._authenticated = False
        self._auth_timestamp = 0

        if was_authenticated:
            logger.info("Master password cache invalidated")
        else:
            logger.debug("Cache already invalidated")

    def extend_cache(self):
        """
        Extend cache time

        Resets the timer to current time, giving another full duration.
        Call this when accessing sensitive items while cache is still valid.
        """
        if self._authenticated:
            old_timestamp = self._auth_timestamp
            self._auth_timestamp = time.time()
            logger.debug(f"Cache extended - reset timer from {old_timestamp} to {self._auth_timestamp}")
        else:
            logger.warning("Attempted to extend cache but not authenticated")

    def get_time_remaining(self) -> int:
        """
        Get remaining cache time in seconds

        Returns:
            Seconds remaining (0 if not authenticated or expired)
        """
        if not self._authenticated:
            return 0

        elapsed = time.time() - self._auth_timestamp
        remaining = self.CACHE_DURATION - elapsed

        return max(0, int(remaining))

    def set_cache_duration(self, seconds: int):
        """
        Set custom cache duration

        Args:
            seconds: Cache duration in seconds (minimum: 60, maximum: 3600)
        """
        # Validate range
        if seconds < 60:
            logger.warning(f"Cache duration too short ({seconds}s), setting to minimum (60s)")
            seconds = 60
        elif seconds > 3600:
            logger.warning(f"Cache duration too long ({seconds}s), setting to maximum (3600s)")
            seconds = 3600

        self.CACHE_DURATION = seconds
        logger.info(f"Cache duration set to {seconds}s")


# === SINGLETON PATTERN ===
# Single global instance for the entire application

_master_auth_cache_instance = None


def get_master_auth_cache() -> MasterAuthCache:
    """
    Get singleton instance of MasterAuthCache

    Use this function to access the cache from anywhere in the application.

    Returns:
        Global MasterAuthCache instance

    Example:
        from core.master_auth_cache import get_master_auth_cache

        cache = get_master_auth_cache()
        if cache.is_authenticated():
            # Proceed without asking password
            pass
    """
    global _master_auth_cache_instance

    if _master_auth_cache_instance is None:
        _master_auth_cache_instance = MasterAuthCache()
        logger.info("Global MasterAuthCache instance created")

    return _master_auth_cache_instance


def invalidate_global_cache():
    """
    Invalidate global cache

    Convenience function for invalidating the global singleton cache.
    Call this on logout or application close.
    """
    cache = get_master_auth_cache()
    cache.invalidate()
