"""Cache implementations with TTL (Time To Live) support."""

import json
import os
import threading
import time
from typing import Any, Callable, Optional


class BaseCache:
    """Base cache interface."""

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set a value with optional TTL in seconds."""
        raise NotImplementedError

    def get(self, key: str) -> Any:
        """Get a value by key."""
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        raise NotImplementedError

    def delete(self, key: str) -> bool:
        """Delete a key. Returns True if key was deleted."""
        raise NotImplementedError

    def clear(self) -> None:
        """Clear all cache entries."""
        raise NotImplementedError

    def cleanup_expired(self) -> int:
        """Remove expired entries. Returns number of entries removed."""
        raise NotImplementedError


class MemoryCache(BaseCache):
    """Thread-safe in-memory cache with TTL support."""

    def __init__(self):
        self.storage: dict[str, dict[str, Any]] = {}
        self.lock = threading.Lock()

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set a value with optional TTL in seconds."""
        expiry_time = time.time() + ttl if ttl else None
        with self.lock:
            self.storage[key] = {"value": value, "expires": expiry_time}

    def get(self, key: str) -> Any:
        """Get a value by key. Returns None if key doesn't exist or expired."""
        with self.lock:
            entry = self.storage.get(key)
            if entry is None:
                return None

            # Check if expired
            if entry["expires"] is not None and time.time() > entry["expires"]:
                # Remove expired entry
                del self.storage[key]
                return None

            return entry["value"]

    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        with self.lock:
            entry = self.storage.get(key)
            if entry is None:
                return False

            # Check if expired
            if entry["expires"] is not None and time.time() > entry["expires"]:
                del self.storage[key]
                return False

            return True

    def delete(self, key: str) -> bool:
        """Delete a key. Returns True if key was deleted."""
        with self.lock:
            if key in self.storage:
                del self.storage[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.storage.clear()

    def cleanup_expired(self) -> int:
        """Remove expired entries. Returns number of entries removed."""
        with self.lock:
            now = time.time()
            expired_keys = [
                key
                for key, entry in self.storage.items()
                if entry["expires"] is not None and now > entry["expires"]
            ]
            for key in expired_keys:
                del self.storage[key]
            return len(expired_keys)


class FileCache(BaseCache):
    """File-based cache with TTL support."""

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or "_nacos_config_cache.json"
        self.lock = threading.Lock()

        # Ensure parent directory exists
        parent_dir = os.path.dirname(self.file_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _read_file(self) -> dict:
        """Read and parse cache file."""
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {k: v for k, v in data.items() if not self._is_expired(v)}

    def _write_file(self, data: dict) -> None:
        """Write cache data to file."""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _is_expired(self, entry: dict) -> bool:
        """Check if a cache entry is expired."""
        expiry = entry.get("expires")
        if expiry is None:
            return False
        return time.time() > expiry

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set a value with optional TTL in seconds."""
        expiry_time = time.time() + ttl if ttl else None
        entry = {"value": value, "expires": expiry_time}

        with self.lock:
            data = self._read_file()
            data[key] = entry
            self._write_file(data)

    def get(self, key: str) -> Any:
        """Get a value by key. Returns None if key doesn't exist or expired."""
        with self.lock:
            data = self._read_file()
            entry = data.get(key)
            if entry is None:
                return None
            if self._is_expired(entry):
                # Remove expired entry and rewrite file
                del data[key]
                self._write_file(data)
                return None
            return entry["value"]

    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        with self.lock:
            data = self._read_file()
            entry = data.get(key)
            if entry is None:
                return False
            if self._is_expired(entry):
                del data[key]
                self._write_file(data)
                return False
            return True

    def delete(self, key: str) -> bool:
        """Delete a key. Returns True if key was deleted."""
        with self.lock:
            data = self._read_file()
            if key in data:
                del data[key]
                self._write_file(data)
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def cleanup_expired(self) -> int:
        """Remove expired entries. Returns number of entries removed."""
        with self.lock:
            data = self._read_file()
            expired_keys = [k for k, v in data.items() if self._is_expired(v)]
            for key in expired_keys:
                del data[key]
            if expired_keys:
                self._write_file(data)
            return len(expired_keys)


# Global cache instances with TTL (default 5 minutes)
DEFAULT_CACHE_TTL = 300  # 5 minutes in seconds

memory_cache = MemoryCache()
