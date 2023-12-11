import asyncio
import hashlib
import logging
import threading
from typing import Optional, Any, Callable

import httpx

from .endpoint import Endpoint
from ..cache import BaseCache, MemoryCache, memory_cache
from ..exception import HTTPResponseError
from ..typings import SyncAsync

logger = logging.getLogger(__name__)


def _get_md5(content):
    return hashlib.md5(content.encode('utf-8')).hexdigest() if content else ''


def _get_config_key(data_id: str, group: str, tenant: str):
    # because `#` is illegal character in Nacos
    return '#'.join([data_id, group, tenant])


def _parse_config_key(key: str):
    return key.split('#')


class _BaseConfigEndpoint(Endpoint):

    def _get(
            self,
            data_id: str,
            group: str,
            tenant: Optional[str] = '',
            *,
            serialized: Optional[bool] = False
    ) -> SyncAsync[Any]:
        return self.client.request(
            "/nacos/v1/cs/configs",
            query={
                "dataId": data_id,
                "group": group,
                "tenant": tenant,
            },
            serialized=serialized
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

    def subscribe(
            self,
            data_id: str,
            group: str,
            tenant: Optional[str] = '',
            timeout: Optional[int] = 30_000,
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
                    last_config = self.get(data_id, group, tenant)
                    last_md5 = _get_md5(last_config)
                    cache.set(config_key, last_config)
                    if callback:
                        callback(last_config)
                except Exception as exc:
                    logging.error(exc)
                    stop_event.wait(1)

        thread = threading.Thread(target=_subscriber)
        thread.start()
        return stop_event

    def get(
            self,
            data_id: str,
            group: str,
            tenant: Optional[str] = '',
            *,
            serialized: Optional[bool] = False,
            cache: Optional[BaseCache] = None,
            default: Optional[str] = None
    ) -> SyncAsync[Any]:
        cache = cache or memory_cache
        config_key = _get_config_key(data_id, group, tenant)
        try:
            config = self._get(data_id, group, tenant, serialized=serialized)
            # todo: this function need to be optimized
            cache.set(config_key, config)
            return config
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.error("Failed to get config from server, try to get from cache. %s", exc)
            return cache.get(config_key)
        except HTTPResponseError as exc:
            logger.debug("Failed to get config from server. %s", exc)
            if exc.status == 404 and default is not None:
                return default
            raise


class ConfigAsyncOperationMixin:

    async def get(
            self,
            data_id: str,
            group: str,
            tenant: Optional[str] = '',
            *,
            serialized: Optional[bool] = False,
            cache: Optional[BaseCache] = None,
            default: Optional[str] = None
    ) -> SyncAsync[Any]:
        cache = cache or memory_cache
        config_key = _get_config_key(data_id, group, tenant)
        try:
            config = await self._get(data_id, group, tenant, serialized=serialized)
            cache.set(config_key, config)
            return config
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.error("Failed to get config from server, try to get from cache. %s", exc)
            return cache.get(config_key)
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
            cache: Optional[BaseCache] = None,
            callback: Optional[Callable] = None
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
                    last_config = await self.get(data_id, group, tenant)
                    last_md5 = _get_md5(last_config)
                    cache.set(config_key, last_config)
                    if callback:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(last_config)
                        else:
                            callback(last_config)
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
