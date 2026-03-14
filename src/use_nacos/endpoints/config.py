"""Config endpoint for Nacos configuration management.

This module provides synchronous and asynchronous operations for managing
configurations in Nacos, including get, publish, delete, and subscribe.
"""

import asyncio
import hashlib
import logging
import threading
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

import httpx

from ..cache import (
    DEFAULT_CACHE_TTL,
    BaseCache,
    MemoryCache,
    memory_cache,
)
from ..exception import HTTPResponseError
from ..serializer import AutoSerializer, Serializer
from ..typings import SyncAsync
from .endpoint import Endpoint

if TYPE_CHECKING:
    from ..client import BaseClient

logger = logging.getLogger(__name__)


def _get_md5(content: Any) -> str:
    """Calculate MD5 hash of the content.

    Args:
        content: Content to hash (string or any object).

    Returns:
        MD5 hash string, or empty string if content is None/empty.
    """
    string_content = str(content) if not isinstance(content, str) else content
    return hashlib.md5(string_content.encode("utf-8")).hexdigest() if content else ""


def _get_config_key(data_id: str, group: str, tenant: str) -> str:
    """Build a unique cache key for a configuration.

    Args:
        data_id: Configuration data ID.
        group: Configuration group.
        tenant: Namespace/tenant ID.

    Returns:
        A unique key string using '#' as separator.
    """
    # because `#` is illegal character in Nacos
    return "#".join([data_id, group, tenant])


def _parse_config_key(key: str) -> list:
    """Parse a cache key back into its components.

    Args:
        key: Cache key string.

    Returns:
        List of [data_id, group, tenant].
    """
    return key.split("#")


def _serialize_config(
    config: Any, serializer: Optional[Union["Serializer", bool]] = None
) -> Any:
    """Serialize configuration content with a serializer.

    Args:
        config: Configuration content to serialize.
        serializer: Serializer instance, True for AutoSerializer, or None.

    Returns:
        Serialized configuration content.
    """
    if isinstance(serializer, bool) and serializer is True:
        serializer = AutoSerializer()
    if isinstance(serializer, Serializer):
        return serializer(config)
    return config


class _BaseConfigEndpoint(Endpoint):
    """Base configuration endpoint with common operations."""

    def _get(
        self, data_id: str, group: str, tenant: Optional[str] = ""
    ) -> SyncAsync[Any]:
        """Get configuration content from Nacos.

        Args:
            data_id: Configuration data ID.
            group: Configuration group.
            tenant: Namespace/tenant ID.

        Returns:
            Configuration content as string.
        """
        return self.client.request(
            "/nacos/v1/cs/configs",
            query={
                "dataId": data_id,
                "group": group,
                "tenant": tenant,
            },
            serialized=False,
        )

    def publish(
        self,
        data_id: str,
        group: str,
        content: str,
        tenant: Optional[str] = "",
        type: Optional[str] = None,
    ) -> SyncAsync[Any]:
        """Publish a configuration.

        Args:
            data_id: Configuration data ID.
            group: Configuration group.
            content: Configuration content.
            tenant: Namespace/tenant ID.
            type: Configuration type (yaml, properties, json, text, etc.).

        Returns:
            True on success.

        Example:
            >>> client.config.publish(
            ...     data_id="app.yaml",
            ...     group="DEFAULT_GROUP",
            ...     content="server:\\n  port: 8080",
            ...     type="yaml"
            ... )
        """
        return self.client.request(
            "/nacos/v1/cs/configs",
            method="POST",
            body={
                "dataId": data_id,
                "group": group,
                "tenant": tenant,
                "content": content,
                "type": type,
            },
        )

    def delete(
        self,
        data_id: str,
        group: str,
        tenant: Optional[str] = "",
    ) -> SyncAsync[Any]:
        """Delete a configuration.

        Args:
            data_id: Configuration data ID.
            group: Configuration group.
            tenant: Namespace/tenant ID.

        Returns:
            True on success.

        Example:
            >>> client.config.delete("app.yaml", "DEFAULT_GROUP")
        """
        return self.client.request(
            "/nacos/v1/cs/configs",
            method="DELETE",
            query={
                "dataId": data_id,
                "group": group,
                "tenant": tenant,
            },
        )

    @staticmethod
    def _format_listening_configs(
        data_id: str,
        group: str,
        content_md5: Optional[str] = None,
        tenant: Optional[str] = "",
    ) -> str:
        """Format listening configuration for long-polling.

        Args:
            data_id: Configuration data ID.
            group: Configuration group.
            content_md5: MD5 hash of current content.
            tenant: Namespace/tenant ID.

        Returns:
            Formatted listening configuration string.
        """
        return "\x02".join([data_id, group, content_md5 or "", tenant]) + "\x01"

    def subscriber(
        self,
        data_id: str,
        group: str,
        content_md5: Optional[str] = None,
        tenant: Optional[str] = "",
        timeout: Optional[int] = 30_000,
    ) -> SyncAsync[Any]:
        """Long-polling for configuration changes.

        This method blocks until a configuration change is detected or timeout.

        Args:
            data_id: Configuration data ID.
            group: Configuration group.
            content_md5: MD5 hash of current content for comparison.
            tenant: Namespace/tenant ID.
            timeout: Long-polling timeout in milliseconds. Defaults to 30000.

        Returns:
            Changed data_id if configuration was updated, empty string otherwise.
        """
        listening_configs = self._format_listening_configs(
            data_id, group, content_md5, tenant
        )
        return self.client.request(
            "/nacos/v1/cs/configs/listener",
            method="POST",
            body={"Listening-Configs": listening_configs},
            headers={
                "Long-Pulling-Timeout": f"{timeout}",
            },
            timeout=timeout,
        )


class ConfigOperationMixin:
    """Mixin for synchronous configuration operations."""

    # Simple client cache for instance requests
    _client_cache: dict = {}

    def __getattr__(self, attr: str) -> SyncAsync[Any]:
        """Allow dynamic attribute access for service-based requests."""
        from functools import partial

        return partial(self.request, service_name=attr)

    @staticmethod
    def _config_callback(
        callback: Optional[Callable], config: Any, serializer: Any
    ) -> None:
        """Invoke callback with serialized configuration.

        Args:
            callback: Callback function to invoke.
            config: Configuration content.
            serializer: Serializer for the configuration.
        """
        if not callable(callback):
            return
        config = _serialize_config(config, serializer)
        callback(config)

    def get(
        self,
        data_id: str,
        group: str,
        tenant: Optional[str] = "",
        *,
        serializer: Optional[Union["Serializer", bool]] = None,
        cache: Optional[BaseCache] = None,
        default: Optional[str] = None,
    ) -> SyncAsync[Any]:
        """Get configuration content.

        Args:
            data_id: Configuration data ID.
            group: Configuration group.
            tenant: Namespace/tenant ID.
            serializer: Serializer to parse the content. True for auto-detection,
                or provide a Serializer instance.
            cache: Cache instance for fallback. Defaults to global memory_cache.
            default: Default value if configuration not found (404) or network
                error with cache miss.

        Returns:
            Configuration content (raw string or serialized based on serializer).
            Returns default value (or None if not provided) when:
            - Configuration not found (404)
            - Network error and cache miss

        Raises:
            HTTPResponseError: If configuration not found and no default provided.

        Example:
            >>> # Get raw content
            >>> content = client.config.get("app.yaml", "DEFAULT_GROUP")
            >>> # Get as dict (auto-detect format)
            >>> config = client.config.get("app.yaml", "DEFAULT_GROUP", serializer=True)
        """
        cache = cache or memory_cache
        config_key = _get_config_key(data_id, group, tenant)
        try:
            config = self._get(data_id, group, tenant)
            # Cache with TTL (default 5 minutes)
            cache.set(config_key, config, ttl=DEFAULT_CACHE_TTL)
            return _serialize_config(config, serializer)
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.error(
                "Failed to get config from server, trying cache. "
                "data_id=%s, group=%s, tenant=%s, error=%s",
                data_id,
                group,
                tenant,
                exc,
            )
            cached = cache.get(config_key)
            if cached is None and default is not None:
                return default
            return _serialize_config(cached, serializer)
        except HTTPResponseError as exc:
            logger.debug(
                "Failed to get config from server. " "data_id=%s, group=%s, status=%d",
                data_id,
                group,
                exc.status,
            )
            if exc.status == 404 and default is not None:
                return default
            raise

    def subscribe(
        self,
        data_id: str,
        group: str,
        tenant: Optional[str] = "",
        timeout: Optional[int] = 30_000,
        serializer: Optional[Union["Serializer", bool]] = None,
        cache: Optional[BaseCache] = None,
        callback: Optional[Callable] = None,
    ) -> SyncAsync[Any]:
        """Subscribe to configuration changes.

        This method starts a background thread that monitors configuration changes
        and invokes the callback when changes are detected.

        Args:
            data_id: Configuration data ID.
            group: Configuration group.
            tenant: Namespace/tenant ID.
            timeout: Long-polling timeout in milliseconds. Defaults to 30000.
            serializer: Serializer for the configuration content.
            cache: Cache instance. Defaults to new MemoryCache.
            callback: Callback function invoked on configuration change.

        Returns:
            A threading.Event object with a cancel() method to stop subscription.

        Example:
            >>> def on_config_change(config):
            ...     print("Config changed:", config)
            >>> stop_event = client.config.subscribe(
            ...     "app.yaml", "DEFAULT_GROUP", callback=on_config_change
            ... )
            >>> # Later, to stop:
            >>> stop_event.cancel()
        """
        cache = cache or MemoryCache()
        config_key = _get_config_key(data_id, group, tenant)
        last_md5 = _get_md5(cache.get(config_key) or "")
        stop_event = threading.Event()
        stop_event.cancel = stop_event.set  # type: ignore[attr-defined]

        def _subscriber() -> None:
            nonlocal last_md5
            while not stop_event.is_set():
                try:
                    response = self.subscriber(
                        data_id, group, last_md5, tenant, timeout
                    )
                    if not response:
                        continue
                    logging.info(
                        "Configuration update detected. "
                        "data_id=%s, group=%s, tenant=%s",
                        data_id,
                        group,
                        tenant,
                    )
                    last_config = self._get(data_id, group, tenant)
                    last_md5 = _get_md5(last_config)
                    # Cache with TTL (default 5 minutes)
                    cache.set(config_key, last_config, ttl=DEFAULT_CACHE_TTL)
                    self._config_callback(callback, last_config, serializer)
                except Exception as exc:
                    logging.error(
                        "Subscription error. data_id=%s, group=%s, error=%s",
                        data_id,
                        group,
                        exc,
                    )
                    stop_event.wait(1)

        thread = threading.Thread(target=_subscriber)
        thread.start()
        return stop_event


class ConfigAsyncOperationMixin:
    """Mixin for asynchronous configuration operations."""

    # Simple client cache for instance requests
    _client_cache: dict = {}

    def __getattr__(self, attr: str) -> SyncAsync[Any]:
        """Allow dynamic attribute access for service-based requests."""
        from functools import partial

        return partial(self.request, service_name=attr)

    @staticmethod
    async def _config_callback(
        callback: Optional[Callable], config: Any, serializer: Any
    ) -> None:
        """Invoke callback with serialized configuration.

        Args:
            callback: Callback function to invoke (sync or async).
            config: Configuration content.
            serializer: Serializer for the configuration.
        """
        if not callable(callback):
            return

        config = _serialize_config(config, serializer)
        if asyncio.iscoroutine_function(callback):
            await callback(config)
        else:
            callback(config)

    async def get(
        self,
        data_id: str,
        group: str,
        tenant: Optional[str] = "",
        *,
        serializer: Optional[Union["Serializer", bool]] = None,
        cache: Optional[BaseCache] = None,
        default: Optional[str] = None,
    ) -> SyncAsync[Any]:
        """Get configuration content asynchronously.

        Args:
            data_id: Configuration data ID.
            group: Configuration group.
            tenant: Namespace/tenant ID.
            serializer: Serializer to parse the content. True for auto-detection,
                or provide a Serializer instance.
            cache: Cache instance for fallback. Defaults to global memory_cache.
            default: Default value if configuration not found (404) or network
                error with cache miss.

        Returns:
            Configuration content (raw string or serialized based on serializer).
            Returns default value (or None if not provided) when:
            - Configuration not found (404)
            - Network error and cache miss

        Raises:
            HTTPResponseError: If configuration not found and no default provided.

        Example:
            >>> # Get raw content
            >>> content = await client.config.get("app.yaml", "DEFAULT_GROUP")
            >>> # Get as dict (auto-detect format)
            >>> config = await client.config.get("app.yaml", "DEFAULT_GROUP", serializer=True)
        """
        cache = cache or memory_cache
        config_key = _get_config_key(data_id, group, tenant)
        try:
            config = await self._get(data_id, group, tenant)
            # Cache with TTL (default 5 minutes)
            cache.set(config_key, config, ttl=DEFAULT_CACHE_TTL)
            return _serialize_config(config, serializer)
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.error(
                "Failed to get config from server, trying cache. "
                "data_id=%s, group=%s, tenant=%s, error=%s",
                data_id,
                group,
                tenant,
                exc,
            )
            cached = cache.get(config_key)
            if cached is None and default is not None:
                return default
            return _serialize_config(cached, serializer)
        except HTTPResponseError as exc:
            logger.debug(
                "Failed to get config from server. " "data_id=%s, group=%s, status=%d",
                data_id,
                group,
                exc.status,
            )
            if exc.status == 404 and default is not None:
                return default
            raise

    async def subscribe(
        self,
        data_id: str,
        group: str,
        tenant: Optional[str] = "",
        timeout: Optional[int] = 30_000,
        serializer: Optional[Union["Serializer", bool]] = None,
        cache: Optional[BaseCache] = None,
        callback: Optional[Callable] = None,
    ) -> SyncAsync[Any]:
        """Subscribe to configuration changes asynchronously.

        This method starts a background task that monitors configuration changes
        and invokes the callback when changes are detected.

        Args:
            data_id: Configuration data ID.
            group: Configuration group.
            tenant: Namespace/tenant ID.
            timeout: Long-polling timeout in milliseconds. Defaults to 30000.
            serializer: Serializer for the configuration content.
            cache: Cache instance. Defaults to new MemoryCache.
            callback: Callback function invoked on configuration change
                (sync or async).

        Returns:
            An asyncio.Event object with a cancel() method to stop subscription.

        Example:
            >>> async def on_config_change(config):
            ...     print("Config changed:", config)
            >>> stop_event = await client.config.subscribe(
            ...     "app.yaml", "DEFAULT_GROUP", callback=on_config_change
            ... )
            >>> # Later, to stop:
            >>> stop_event.cancel()
        """
        cache = cache or MemoryCache()
        config_key = _get_config_key(data_id, group, tenant)
        last_md5 = _get_md5(cache.get(config_key) or "")
        stop_event = asyncio.Event()

        async def _async_subscriber() -> None:
            nonlocal last_md5
            while True:
                try:
                    response = await self.subscriber(
                        data_id, group, last_md5, tenant, timeout
                    )
                    if not response:
                        continue
                    logging.info(
                        "Configuration update detected. "
                        "data_id=%s, group=%s, tenant=%s",
                        data_id,
                        group,
                        tenant,
                    )
                    last_config = await self._get(data_id, group, tenant)
                    last_md5 = _get_md5(last_config)
                    # Cache with TTL (default 5 minutes)
                    cache.set(config_key, last_config, ttl=DEFAULT_CACHE_TTL)
                    await self._config_callback(callback, last_config, serializer)
                except asyncio.CancelledError:
                    break
                except Exception as exc:
                    logging.error(
                        "Subscription error. "
                        "data_id=%s, group=%s, tenant=%s, error=%s",
                        data_id,
                        group,
                        tenant,
                        exc,
                    )
                    await asyncio.sleep(1)

        task = asyncio.create_task(_async_subscriber())

        def cancel() -> None:
            task.cancel()

        stop_event.cancel = cancel  # type: ignore[attr-defined]
        return stop_event


class ConfigEndpoint(_BaseConfigEndpoint, ConfigOperationMixin):
    """Synchronous configuration endpoint.

    Provides methods for getting, publishing, deleting, and subscribing
    to configurations in Nacos.
    """

    pass


class ConfigAsyncEndpoint(_BaseConfigEndpoint, ConfigAsyncOperationMixin):
    """Asynchronous configuration endpoint.

    Provides async methods for getting, publishing, deleting, and
    subscribing to configurations in Nacos.
    """

    pass