"""Test cache TTL functionality."""

import time

import pytest

from use_nacos.cache import DEFAULT_CACHE_TTL, FileCache, MemoryCache


@pytest.fixture
def memory_cache():
    return MemoryCache()


@pytest.fixture
def file_cache(tmp_path):
    import os

    return FileCache(file_path=tmp_path)


def test_memory_cache_set_get(memory_cache):
    """Test basic set and get operations."""
    memory_cache.set("key1", "value1")
    assert memory_cache.get("key1") == "value1"
    assert memory_cache.exists("key1") is True


def test_memory_cache_ttl(memory_cache):
    """Test that cache entries expire."""
    # Set with 0.1 second TTL
    memory_cache.set("ttl_key", "ttl_value", ttl=0.1)

    # Should exist immediately
    assert memory_cache.get("ttl_key") == "ttl_value"
    assert memory_cache.exists("ttl_key") is True

    # Wait for expiration
    time.sleep(0.15)

    # Should be expired now
    assert memory_cache.get("ttl_key") is None
    assert memory_cache.exists("ttl_key") is False


def test_memory_cache_no_ttl(memory_cache):
    """Test that cache entries without TTL persist."""
    memory_cache.set("no_ttl_key", "no_ttl_value", ttl=None)

    # Wait longer than default TTL
    time.sleep(0.2)

    # Should still exist (no expiration)
    assert memory_cache.get("no_ttl_key") == "no_ttl_value"
    assert memory_cache.exists("no_ttl_key") is True


def test_memory_cache_delete(memory_cache):
    """Test delete operation."""
    memory_cache.set("delete_key", "delete_value")
    assert memory_cache.exists("delete_key") is True

    result = memory_cache.delete("delete_key")
    assert result is True
    assert memory_cache.exists("delete_key") is False

    # Delete non-existent key
    result = memory_cache.delete("nonexistent")
    assert result is False


def test_memory_cache_clear(memory_cache):
    """Test clear operation."""
    memory_cache.set("key1", "value1")
    memory_cache.set("key2", "value2")
    memory_cache.set("key3", "value3")

    memory_cache.clear()

    assert memory_cache.get("key1") is None
    assert memory_cache.get("key2") is None
    assert memory_cache.get("key3") is None


def test_memory_cache_cleanup_expired(memory_cache):
    """Test cleanup_expired operation."""
    # Add multiple entries with different TTLs
    memory_cache.set("expiring1", "value1", ttl=0.1)
    memory_cache.set("expiring2", "value2", ttl=0.1)
    memory_cache.set("persistent", "value3", ttl=None)

    # Wait for expiration
    time.sleep(0.15)

    # Cleanup should remove 2 entries
    removed = memory_cache.cleanup_expired()
    assert removed == 2

    # Check state
    assert memory_cache.get("expiring1") is None
    assert memory_cache.get("expiring2") is None
    assert memory_cache.get("persistent") == "value3"


def test_file_cache_ttl(file_cache, tmp_path):
    """Test FileCache TTL."""
    import os
    import shutil
    import tempfile

    # Create a dedicated temp file for testing
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = f.name
        f.write("{}")

    try:
        cache_instance = FileCache(file_path=temp_path)

        # Set with 0.1 second TTL
        cache_instance.set("ttl_key", "ttl_value", ttl=0.1)

        # Should exist immediately
        assert cache_instance.get("ttl_key") == "ttl_value"
        assert cache_instance.exists("ttl_key") is True

        # Wait for expiration
        time.sleep(0.15)

        # Should be expired now
        assert cache_instance.get("ttl_key") is None
        assert cache_instance.exists("ttl_key") is False
    finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
            if os.path.isdir(temp_path):
                shutil.rmtree(temp_path)
            else:
                os.remove(temp_path)


def test_default_cache_ttl():
    """Test DEFAULT_CACHE_TTL constant."""
    assert DEFAULT_CACHE_TTL == 300  # 5 minutes in seconds
