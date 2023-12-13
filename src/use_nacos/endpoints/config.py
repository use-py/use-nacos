import asyncio
import hashlib
import logging
import threading
from typing import Optional, Any, Callable, Union

import httpx

from .endpoint import Endpoint
from ..cache import BaseCache, MemoryCache, memory_cache
from ..exception import HTTPResponseError
from ..serializer import Serializer, AutoSerializer
from ..typings import SyncAsync

logger = logging.getLogger(__name__)


def _get_md5(content: Any):
    string_content = str(content) if not isinstance(content, str) else content
    return hashlib.md5(string_content.encode('utf-8')).hexdigest() if content else ''


def _get_config_key(data_id: str, group: str, tenant: str):
    # because `#` is illegal character in Nacos
    return '#'.join([data_id, group, tenant])


def _parse_config_key(key: str):
    return key.split('#')


def _serialize_config(
        config: Any,
        serializer: Optional[Union["Serializer", bool]] = None
):
    """ Serialize config with serializer """
    if isinstance(serializer, bool) and serializer is True:
        serializer = AutoSerializer()
    if isinstance(serializer, Serializer):
        return serializer(config)
    return config


class _BaseConfigEndpoint(Endpoint):

    def _get(
            self,
            data_id: str,
            group: str,
            tenant: Optional[str] = ''
    ) -> SyncAsync[Any]:
        return self.client.request(
            "/nacos/v1/cs/configs",
            query={
                "dataId": data_id,
                "group": group,
                "tenant": tenant,
            },
            serialized=False
        )

    def publish(
            self,
            data_id: str,
            group: str,
            content: str,
            tenant: Optional[str] = '',
            type: Optional[str] = None,
    ) -> SyncAsync[Any]:
        return self.client.request(
            "/nacos/v1/cs/configs",
            method="POST",
            body={
                "dataId": data_id,
                "group": group,
                "tenant": tenant,
                "content": content,
                "type": type,
            }
        )

    def delete(
            self,
            data_id: str,
            group: str,
            tenant: Optional[str] = '',
    ) -> SyncAsync[Any]:
        return self.client.request(
            "/nacos/v1/cs/configs",
            method="DELETE",
            query={
                "dataId": data_id,
                "group": group,
                "tenant": tenant,
            }
        )

    @staticmethod
    def _format_listening_configs(
            data_id: str,
            group: str,
            content_md5: Optional[str] = None,
            tenant: Optional[str] = ''
    ) -> str:
        return u'\x02'.join([data_id, group, content_md5 or "", tenant]) + u'\x01'

    def subscriber(
            self,
            data_id: str,
            group: str,
            content_md5: Optional[str] = None,
            tenant: Optional[str] = '',
            timeout: Optional[int] = 30_000,
    ) -> SyncAsync[Any]:
        listening_configs = self._format_listening_configs(
            data_id, group, content_md5, tenant
        )
        return self.client.request(
            "/nacos/v1/cs/configs/listener",
            method="POST",
            body={
                "Listening-Configs": listening_configs
            },
            headers={
                "Long-Pulling-Timeout": f"{timeout}",
            },
            timeout=timeout
        )


class ConfigOperationMixin:

    @staticmethod
    def _config_callback(callback, config, serializer):
        if not callable(callback):
            return
        config = _serialize_config(config, serializer)
        callback(config)

    def get(
            self,
            data_id: str,
            group: str,
            tenant: Optional[str] = '',
            *,
            serializer: Optional[Union["Serializer", bool]] = None,
            cache: Optional[BaseCache] = None,
            default: Optional[str] = None
    ) -> SyncAsync[Any]:
        cache = cache or memory_cache
        config_key = _get_config_key(data_id, group, tenant)
        try:
            config = self._get(data_id, group, tenant)
            # todo: this function need to be optimized
            cache.set(config_key, config)
            return _serialize_config(config, serializer)
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.error("Failed to get config from server, try to get from cache. %s", exc)
            return _serialize_config(cache.get(config_key), serializer)
        except HTTPResponseError as exc:
            logger.debug("Failed to get config from server. %s", exc)
            if exc.status == 404 and default is not None:
                return default
            raise

    def subscribe(
            self,
            data_id: str,
            group: str,
            tenant: Optional[str] = '',
            timeout: Optional[int] = 30_000,
            serializer: Optional[Union["Serializer", bool]] = None,
            cache: Optional[BaseCache] = None,
            callback: Optional[Callable] = None
    ) -> SyncAsync[Any]:
        cache = cache or MemoryCache()
        config_key = _get_config_key(data_id, group, tenant)
        last_md5 = _get_md5(cache.get(config_key) or '')
        stop_event = threading.Event()
        stop_event.cancel = stop_event.set

        def _subscriber():
            nonlocal last_md5
            while not stop_event.is_set():
                try:
                    response = self.subscriber(data_id, group, last_md5, tenant, timeout)
                    if not response:
                        continue
                    logging.info("Configuration update detected.")
                    last_config = self._get(data_id, group, tenant)
                    last_md5 = _get_md5(last_config)
                    cache.set(config_key, last_config)
                    self._config_callback(callback, last_config, serializer)
                except Exception as exc:
                    logging.error(exc)
                    stop_event.wait(1)

        thread = threading.Thread(target=_subscriber)
        thread.start()
        return stop_event


class ConfigAsyncOperationMixin:

    @staticmethod
    async def _config_callback(callback, config, serializer):
        if not callable(callback):
            return

        config = _serialize_config(config, serializer)
        if asyncio.iscoroutinefunction(callback):
            await callback(config)
        else:
            callback(config)

    async def get(
            self,
            data_id: str,
            group: str,
            tenant: Optional[str] = '',
            *,
            serializer: Optional[Union["Serializer", bool]] = None,
            cache: Optional[BaseCache] = None,
            default: Optional[str] = None
    ) -> SyncAsync[Any]:
        cache = cache or memory_cache
        config_key = _get_config_key(data_id, group, tenant)
        try:
            config = await self._get(data_id, group, tenant)
            cache.set(config_key, config)
            return _serialize_config(config, serializer)
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.error("Failed to get config from server, try to get from cache. %s", exc)
            return _serialize_config(cache.get(config_key), serializer)
        except HTTPResponseError as exc:
            logger.debug("Failed to get config from server. %s", exc)
            if exc.status == 404 and default is not None:
                return default
            raise

    async def subscribe(
            self,
            data_id: str,
            group: str,
            tenant: Optional[str] = '',
            timeout: Optional[int] = 30_000,
            serializer: Optional[Union["Serializer", bool]] = None,
            cache: Optional[BaseCache] = None,
            callback: Optional[Callable] = None,
    ) -> SyncAsync[Any]:
        cache = cache or MemoryCache()
        config_key = _get_config_key(data_id, group, tenant)
        last_md5 = _get_md5(cache.get(config_key) or '')
        stop_event = threading.Event()
        stop_event.cancel = stop_event.set

        async def _async_subscriber():
            nonlocal last_md5
            while True:
                try:
                    response = await self.subscriber(
                        data_id, group, last_md5, tenant, timeout
                    )
                    if not response:
                        continue
                    logging.info("Configuration update detected.")
                    last_config = await self._get(data_id, group, tenant)
                    last_md5 = _get_md5(last_config)
                    cache.set(config_key, last_config)
                    await self._config_callback(callback, last_config, serializer)
                except asyncio.CancelledError:
                    break
                except Exception as exc:
                    logging.error(exc)
                    await asyncio.sleep(1)

        return asyncio.create_task(_async_subscriber())


class ConfigEndpoint(_BaseConfigEndpoint, ConfigOperationMixin):
    ...


class ConfigAsyncEndpoint(_BaseConfigEndpoint, ConfigAsyncOperationMixin):
    ...
