"""Instance endpoint for Nacos service instance management.

This module provides synchronous and asynchronous operations for managing
service instances in Nacos, including registration, discovery, and health checks.
"""

import asyncio
import json
import logging
import threading
import time
from functools import partial
from typing import TYPE_CHECKING, Any, List, Literal, Optional, TypedDict

import httpx

from .._chooser import Chooser
from ..exception import EmptyHealthyInstanceError
from ..typings import BeatType, SyncAsync
from .endpoint import Endpoint

if TYPE_CHECKING:
    from ..client import BaseClient

_ConsistencyType = Literal["ephemeral", "persist"]

logger = logging.getLogger(__name__)


class InstanceType(TypedDict):
    """Type definition for a Nacos service instance.

    Attributes:
        ip: Instance IP address.
        port: Instance port number.
        weight: Instance weight for load balancing.
        enabled: Whether the instance is enabled.
        healthy: Whether the instance is healthy.
        metadata: Instance metadata as a dictionary.
    """

    ip: str
    port: int
    weight: float
    enabled: bool
    healthy: bool
    metadata: Optional[dict]


def _choose_one_healthy(instances: List[InstanceType]) -> InstanceType:
    """Choose one healthy instance using weighted random selection.

    Args:
        instances: List of instance dictionaries.

    Returns:
        Selected instance dictionary.

    Raises:
        EmptyHealthyInstanceError: If no healthy instances are available.
    """
    hosts = [(host, host.get("weight")) for host in instances]
    if not hosts:
        raise EmptyHealthyInstanceError("No healthy instance found")
    chooser = Chooser(hosts)
    chooser.refresh()
    return chooser.random_with_weight()


class InstanceOperationMixin:
    """Mixin for synchronous instance operations."""

    # Simple client cache for instance requests
    _client_cache: dict = {}

    def __getattr__(self, attr: str) -> SyncAsync[Any]:
        """Allow dynamic attribute access for service-based requests.

        This enables syntax like: client.instance.myservice.get("/api")
        """
        return partial(self.request, service_name=attr)

    def _get_client(self, instance: InstanceType) -> httpx.Client:
        """Get or create a cached httpx client for the instance.

        Args:
            instance: Instance dictionary with ip and port.

        Returns:
            An httpx.Client for making requests to this instance.
        """
        cache_key = (instance["ip"], instance["port"])
        if cache_key not in self._client_cache:
            self._client_cache[cache_key] = httpx.Client()
        return self._client_cache[cache_key]

    def request(
        self,
        method: str,
        path: str,
        instance: Optional[InstanceType] = None,
        service_name: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> SyncAsync[Any]:
        """Make an HTTP request to a service instance.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: Request path.
            instance: Specific instance to use. If None, a healthy instance
                will be selected from the service.
            service_name: Service name for instance discovery.
            *args: Additional positional arguments for httpx.request.
            **kwargs: Additional keyword arguments for httpx.request.

        Returns:
            HTTP response from the instance.

        Raises:
            ValueError: If neither instance nor service_name is provided.
        """
        if not any([instance, service_name]):
            raise ValueError("Either `instance` or `service_name` should be provided")
        if not instance:
            instance = self.get_one_healthy(service_name)  # type: ignore[assignment]
        url = f"http://{instance['ip']}:{instance['port']}{path}"  # noqa
        client = self._get_client(instance)
        return client.request(method=method, url=url, *args, **kwargs)

    def heartbeat(
        self,
        service_name: str,
        ip: str,
        port: int,
        weight: Optional[float] = 1.0,
        namespace_id: Optional[str] = "",
        group_name: Optional[str] = None,
        ephemeral: Optional[bool] = True,
        interval: Optional[int] = 1_000,
        skip_exception: Optional[bool] = True,
        **kwargs: Any,
    ) -> SyncAsync[Any]:
        """Start a background heartbeat thread for an ephemeral instance.

        This method starts a daemon thread that sends periodic heartbeats
        to keep the ephemeral instance registered.

        Args:
            service_name: Service name for the instance.
            ip: Instance IP address.
            port: Instance port number.
            weight: Instance weight. Defaults to 1.0.
            namespace_id: Namespace ID. Defaults to empty string.
            group_name: Group name for the service.
            ephemeral: Whether the instance is ephemeral. Defaults to True.
            interval: Heartbeat interval in milliseconds. Defaults to 1000.
            skip_exception: Whether to skip exceptions and continue. Defaults to True.
            **kwargs: Additional parameters for the beat request.

        Returns:
            A threading.Event object with a cancel() method to stop heartbeats.

        Example:
            >>> stop_event = client.instance.heartbeat(
            ...     "my-service", "192.168.1.100", 8080
            ... )
            >>> # Later, to stop:
            >>> stop_event.cancel()
        """
        stop_event = threading.Event()
        stop_event.cancel = stop_event.set  # type: ignore[attr-defined]

        def _heartbeat() -> None:
            while not stop_event.is_set():
                time.sleep(interval / 1_000)
                try:
                    self.beat(
                        service_name=service_name,
                        ip=ip,
                        port=port,
                        weight=weight,
                        namespace_id=namespace_id,
                        group_name=group_name,
                        ephemeral=ephemeral,
                        **kwargs,
                    )
                except Exception as exc:
                    logger.error(
                        "Heartbeat error. " "service_name=%s, ip=%s, port=%d, error=%s",
                        service_name,
                        ip,
                        port,
                        exc,
                    )
                    if skip_exception:
                        continue
                    raise exc

        thread = threading.Thread(target=_heartbeat)
        thread.start()
        return stop_event

    def get_one_healthy(
        self,
        service_name: str,
        namespace_id: Optional[str] = None,
        group_name: Optional[str] = None,
        clusters: Optional[str] = None,
    ) -> InstanceType:
        """Get a single healthy instance using weighted random selection.

        Args:
            service_name: Service name to query.
            namespace_id: Namespace ID.
            group_name: Group name for the service.
            clusters: Comma-separated list of cluster names.

        Returns:
            Selected instance dictionary.

        Raises:
            EmptyHealthyInstanceError: If no healthy instances are available.

        Example:
            >>> instance = client.instance.get_one_healthy("my-service")
            >>> print(instance["ip"], instance["port"])
        """
        instances = self.list(
            service_name=service_name,
            namespace_id=namespace_id,
            group_name=group_name,
            clusters=clusters,
            healthy_only=True,
        )
        return _choose_one_healthy(instances["hosts"])


class InstanceAsyncOperationMixin:
    """Mixin for asynchronous instance operations."""

    # Simple client cache for instance requests
    _client_cache: dict = {}

    def __getattr__(self, attr: str) -> SyncAsync[Any]:
        """Allow dynamic attribute access for service-based requests.

        This enables syntax like: await client.instance.myservice.get("/api")
        """
        return partial(self.request, service_name=attr)

    async def _get_client(self, instance: InstanceType) -> httpx.AsyncClient:
        """Get or create a cached async httpx client for the instance.

        Args:
            instance: Instance dictionary with ip and port.

        Returns:
            An httpx.AsyncClient for making requests to this instance.
        """
        cache_key = (instance["ip"], instance["port"])
        if cache_key not in self._client_cache:
            self._client_cache[cache_key] = httpx.AsyncClient()
        return self._client_cache[cache_key]

    async def request(
        self,
        method: str,
        path: str,
        instance: Optional[InstanceType] = None,
        service_name: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> SyncAsync[Any]:
        """Make an async HTTP request to a service instance.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: Request path.
            instance: Specific instance to use. If None, a healthy instance
                will be selected from the service.
            service_name: Service name for instance discovery.
            *args: Additional positional arguments for httpx.request.
            **kwargs: Additional keyword arguments for httpx.request.

        Returns:
            HTTP response from the instance.

        Raises:
            ValueError: If neither instance nor service_name is provided.
        """
        if not any([instance, service_name]):
            raise ValueError("Either `instance` or `service_name` should be provided")
        if not instance:
            instance = await self.get_one_healthy(service_name)  # type: ignore[assignment,misc]
        url = f"http://{instance['ip']}:{instance['port']}{path}"  # noqa
        client = await self._get_client(instance)
        return await client.request(method=method, url=url, *args, **kwargs)

    async def heartbeat(
        self,
        service_name: str,
        ip: str,
        port: int,
        weight: Optional[float] = 1.0,
        namespace_id: Optional[str] = "",
        group_name: Optional[str] = None,
        ephemeral: Optional[bool] = True,
        interval: Optional[int] = 1_000,
        skip_exception: Optional[bool] = True,
        **kwargs: Any,
    ) -> SyncAsync[Any]:
        """Start a background heartbeat task for an ephemeral instance.

        This method creates an async task that sends periodic heartbeats
        to keep the ephemeral instance registered.

        Args:
            service_name: Service name for the instance.
            ip: Instance IP address.
            port: Instance port number.
            weight: Instance weight. Defaults to 1.0.
            namespace_id: Namespace ID. Defaults to empty string.
            group_name: Group name for the service.
            ephemeral: Whether the instance is ephemeral. Defaults to True.
            interval: Heartbeat interval in milliseconds. Defaults to 1000.
            skip_exception: Whether to skip exceptions and continue. Defaults to True.
            **kwargs: Additional parameters for the beat request.

        Returns:
            An asyncio.Task object that can be cancelled.

        Example:
            >>> task = await client.instance.heartbeat(
            ...     "my-service", "192.168.1.100", 8080
            ... )
            >>> # Later, to stop:
            >>> task.cancel()
        """
        stop_event = threading.Event()
        stop_event.cancel = stop_event.set  # type: ignore[attr-defined]

        async def _async_heartbeat() -> None:
            while True:
                await asyncio.sleep(interval / 1_000)
                try:
                    await self.beat(
                        service_name=service_name,
                        ip=ip,
                        port=port,
                        weight=weight,
                        namespace_id=namespace_id,
                        group_name=group_name,
                        ephemeral=ephemeral,
                        **kwargs,
                    )
                except asyncio.CancelledError:
                    break
                except Exception as exc:
                    logger.error(
                        "Heartbeat error. " "service_name=%s, ip=%s, port=%d, error=%s",
                        service_name,
                        ip,
                        port,
                        exc,
                    )
                    if skip_exception:
                        continue
                    raise exc

        return asyncio.create_task(_async_heartbeat())

    async def get_one_healthy(
        self,
        service_name: str,
        namespace_id: Optional[str] = None,
        group_name: Optional[str] = None,
        clusters: Optional[str] = None,
    ) -> InstanceType:
        """Get a single healthy instance using weighted random selection.

        Args:
            service_name: Service name to query.
            namespace_id: Namespace ID.
            group_name: Group name for the service.
            clusters: Comma-separated list of cluster names.

        Returns:
            Selected instance dictionary.

        Raises:
            EmptyHealthyInstanceError: If no healthy instances are available.

        Example:
            >>> instance = await client.instance.get_one_healthy("my-service")
            >>> print(instance["ip"], instance["port"])
        """
        instances = await self.list(
            service_name=service_name,
            namespace_id=namespace_id,
            group_name=group_name,
            clusters=clusters,
            healthy_only=True,
        )
        return _choose_one_healthy(instances["hosts"])


class _BaseInstanceEndpoint(Endpoint):
    """Base endpoint for instance management operations."""

    def register(
        self,
        service_name: str,
        ip: str,
        port: int,
        namespace_id: Optional[str] = "",
        weight: Optional[float] = 1.0,
        enabled: Optional[bool] = True,
        healthy: Optional[bool] = True,
        metadata: Optional[str] = None,
        cluster_name: Optional[str] = None,
        group_name: Optional[str] = None,
        ephemeral: Optional[bool] = None,
    ) -> SyncAsync[Any]:
        """Register a service instance.

        Args:
            service_name: Service name for the instance.
            ip: Instance IP address.
            port: Instance port number.
            namespace_id: Namespace ID. Defaults to empty string.
            weight: Instance weight for load balancing. Defaults to 1.0.
            enabled: Whether the instance is enabled. Defaults to True.
            healthy: Whether the instance is healthy. Defaults to True.
            metadata: Instance metadata as JSON string.
            cluster_name: Cluster name for the instance.
            group_name: Group name for the service.
            ephemeral: Whether the instance is ephemeral. Defaults to True for
                ephemeral instances (requires heartbeat), False for persistent.

        Returns:
            "ok" on success.

        Example:
            >>> client.instance.register(
            ...     "my-service",
            ...     "192.168.1.100",
            ...     8080,
            ...     metadata='{"version":"1.0"}'
            ... )
        """
        return self.client.request(
            "/nacos/v1/ns/instance",
            method="POST",
            query={
                "ip": ip,
                "port": port,
                "serviceName": service_name,
                "namespaceId": namespace_id,
                "weight": weight,
                "enabled": enabled,
                "healthy": healthy,
                "metadata": metadata,
                "clusterName": cluster_name,
                "groupName": group_name,
                "ephemeral": ephemeral,
            },
        )

    def delete(
        self,
        service_name: str,
        ip: str,
        port: int,
        group_name: Optional[str] = None,
        cluster_name: Optional[str] = None,
        namespace_id: Optional[str] = None,
        ephemeral: Optional[bool] = None,
    ) -> SyncAsync[Any]:
        """Deregister a service instance.

        Args:
            service_name: Service name for the instance.
            ip: Instance IP address.
            port: Instance port number.
            group_name: Group name for the service.
            cluster_name: Cluster name for the instance.
            namespace_id: Namespace ID.
            ephemeral: Whether the instance is ephemeral.

        Returns:
            "ok" on success.

        Example:
            >>> client.instance.delete("my-service", "192.168.1.100", 8080)
        """
        return self.client.request(
            "/nacos/v1/ns/instance",
            method="DELETE",
            query={
                "serviceName": service_name,
                "ip": ip,
                "port": port,
                "groupName": group_name,
                "clusterName": cluster_name,
                "namespaceId": namespace_id,
                "ephemeral": ephemeral,
            },
        )

    def list(
        self,
        service_name: str,
        namespace_id: Optional[str] = None,
        group_name: Optional[str] = None,
        clusters: Optional[str] = None,
        healthy_only: Optional[bool] = False,
    ) -> SyncAsync[Any]:
        """List instances for a service.

        Args:
            service_name: Service name to query.
            namespace_id: Namespace ID.
            group_name: Group name for the service.
            clusters: Comma-separated list of cluster names.
            healthy_only: Whether to return only healthy instances. Defaults to False.

        Returns:
            A dict containing:
                - name: Service name
                - hosts: List of instance dictionaries

        Example:
            >>> result = client.instance.list("my-service")
            >>> for host in result["hosts"]:
            ...     print(host["ip"], host["port"])
        """
        return self.client.request(
            "/nacos/v1/ns/instance/list",
            query={
                "serviceName": service_name,
                "namespaceId": namespace_id,
                "groupName": group_name,
                "clusters": clusters,
                "healthyOnly": healthy_only,
            },
        )

    def update(
        self,
        service_name: str,
        ip: str,
        port: int,
        namespace_id: Optional[str] = None,
        weight: Optional[float] = None,
        enabled: Optional[bool] = None,
        metadata: Optional[dict] = None,
        cluster_name: Optional[str] = None,
        group_name: Optional[str] = None,
        ephemeral: Optional[bool] = None,
    ) -> SyncAsync[Any]:
        """Update an instance's properties.

        Args:
            service_name: Service name for the instance.
            ip: Instance IP address.
            port: Instance port number.
            namespace_id: Namespace ID.
            weight: New weight for the instance.
            enabled: Whether the instance is enabled.
            metadata: New metadata dictionary.
            cluster_name: Cluster name for the instance.
            group_name: Group name for the service.
            ephemeral: Whether the instance is ephemeral.

        Returns:
            "ok" on success.

        Example:
            >>> client.instance.update(
            ...     "my-service",
            ...     "192.168.1.100",
            ...     8080,
            ...     weight=2.0,
            ...     metadata={"version": "2.0"}
            ... )
        """
        return self.client.request(
            "/nacos/v1/ns/instance",
            method="PUT",
            query={
                "ip": ip,
                "port": port,
                "serviceName": service_name,
                "namespaceId": namespace_id,
                "weight": weight,
                "enabled": enabled,
                "metadata": metadata,
                "clusterName": cluster_name,
                "groupName": group_name,
                "ephemeral": ephemeral,
            },
        )

    def get(
        self,
        service_name: str,
        ip: str,
        port: int,
        namespace_id: Optional[str] = "",
        group_name: Optional[str] = None,
        cluster: Optional[str] = None,
        healthy_only: Optional[bool] = False,
        ephemeral: Optional[bool] = None,
    ) -> SyncAsync[Any]:
        """Get details of a specific instance.

        Args:
            service_name: Service name for the instance.
            ip: Instance IP address.
            port: Instance port number.
            namespace_id: Namespace ID. Defaults to empty string.
            group_name: Group name for the service.
            cluster: Cluster name for the instance.
            healthy_only: Whether to check health status.
            ephemeral: Whether the instance is ephemeral.

        Returns:
            Instance details dictionary.

        Example:
            >>> instance = client.instance.get(
            ...     "my-service", "192.168.1.100", 8080
            ... )
        """
        return self.client.request(
            "/nacos/v1/ns/instance",
            query={
                "serviceName": service_name,
                "ip": ip,
                "port": port,
                "namespaceId": namespace_id,
                "groupName": group_name,
                "cluster": cluster,
                "healthyOnly": healthy_only,
                "ephemeral": ephemeral,
            },
        )

    def beat(
        self,
        service_name: str,
        ip: str,
        port: int,
        weight: Optional[float] = 1.0,
        namespace_id: Optional[str] = "",
        group_name: Optional[str] = None,
        ephemeral: Optional[bool] = None,
        **kwargs: Any,
    ) -> SyncAsync[Any]:
        """Send a heartbeat for an ephemeral instance.

        Heartbeats are required to keep ephemeral instances registered.
        If no heartbeat is received within the timeout period, the instance
        will be automatically deregistered.

        Args:
            service_name: Service name for the instance.
            ip: Instance IP address.
            port: Instance port number.
            weight: Instance weight. Defaults to 1.0.
            namespace_id: Namespace ID. Defaults to empty string.
            group_name: Group name for the service.
            ephemeral: Whether the instance is ephemeral.
            **kwargs: Additional beat parameters.

        Returns:
            Heartbeat response from the server.

        Note:
            For automatic heartbeats, use the heartbeat() method instead.

        Example:
            >>> client.instance.beat("my-service", "192.168.1.100", 8080)
        """
        # see: https://github.com/alibaba/nacos/issues/10448#issuecomment-1538178112
        serverName = f"{group_name}@@{service_name}" if group_name else service_name
        beat_params: BeatType = {
            "serviceName": serverName,
            "ip": ip,
            "port": port,
            "weight": weight,  # type: ignore[typeddict-item]
            "ephemeral": ephemeral,  # type: ignore[typeddict-item]
            **kwargs,  # type: ignore[typeddict-item]
        }
        return self.client.request(
            "/nacos/v1/ns/instance/beat",
            method="PUT",
            query={
                "serviceName": serverName,
                "beat": json.dumps(beat_params),
                "namespaceId": namespace_id,
                "groupName": group_name,
            },
        )

    def update_health(
        self,
        service_name: str,
        ip: str,
        port: int,
        healthy: bool,
        namespace_id: Optional[str] = "",
        group_name: Optional[str] = None,
        cluster_name: Optional[str] = None,
    ) -> SyncAsync[Any]:
        """Update the health status of a persistent instance.

        Note: This only works for persistent instances, not ephemeral ones.
        Ephemeral instance health is determined by heartbeats.

        Args:
            service_name: Service name for the instance.
            ip: Instance IP address.
            port: Instance port number.
            healthy: New health status (True or False).
            namespace_id: Namespace ID. Defaults to empty string.
            group_name: Group name for the service.
            cluster_name: Cluster name for the instance.

        Returns:
            "ok" on success.

        Example:
            >>> client.instance.update_health(
            ...     "my-service", "192.168.1.100", 8080, healthy=False
            ... )
        """
        return self.client.request(
            "/nacos/v1/ns/health/instance",
            method="PUT",
            query={
                "serviceName": service_name,
                "ip": ip,
                "port": port,
                "healthy": healthy,
                "namespaceId": namespace_id,
                "groupName": group_name,
                "clusterName": cluster_name,
            },
        )

    def batch_update_metadata(
        self,
        service_name: str,
        namespace_id: str,
        metadata: dict,
        consistency_type: Optional["_ConsistencyType"] = None,
        instances: Optional[list] = None,
    ) -> SyncAsync[Any]:
        """Batch update metadata for multiple instances.

        Args:
            service_name: Service name for the instances.
            namespace_id: Namespace ID.
            metadata: Metadata dictionary to update.
            consistency_type: "ephemeral" or "persist".
            instances: List of instance dictionaries with ip and port.

        Returns:
            Update result from the server.

        Example:
            >>> client.instance.batch_update_metadata(
            ...     "my-service",
            ...     "dev",
            ...     {"region": "us-west"},
            ...     instances=[{"ip": "192.168.1.100", "port": 8080}]
            ... )
        """
        return self.client.request(
            "/nacos/v1/ns/instance/metadata/batch",
            method="PUT",
            query={
                "serviceName": service_name,
                "namespaceId": namespace_id,
                "metadata": json.dumps(metadata),
                "consistencyType": consistency_type,
                "instances": json.dumps(instances),
            },
        )

    def batch_delete_metadata(
        self,
        service_name: str,
        namespace_id: str,
        metadata: dict,
        consistency_type: Optional["_ConsistencyType"] = None,
        instances: Optional[list] = None,
    ) -> SyncAsync[Any]:
        """Batch delete metadata keys from multiple instances.

        Args:
            service_name: Service name for the instances.
            namespace_id: Namespace ID.
            metadata: Dictionary of metadata keys to delete (values ignored).
            consistency_type: "ephemeral" or "persist".
            instances: List of instance dictionaries with ip and port.

        Returns:
            Delete result from the server.

        Example:
            >>> client.instance.batch_delete_metadata(
            ...     "my-service",
            ...     "dev",
            ...     {"temp_key": ""},
            ...     instances=[{"ip": "192.168.1.100", "port": 8080}]
            ... )
        """
        return self.client.request(
            "/nacos/v1/ns/instance/metadata/batch",
            method="DELETE",
            query={
                "serviceName": service_name,
                "namespaceId": namespace_id,
                "metadata": json.dumps(metadata),
                "consistencyType": consistency_type,
                "instances": json.dumps(instances),
            },
        )


class InstanceEndpoint(_BaseInstanceEndpoint, InstanceOperationMixin):
    """Synchronous instance endpoint for Nacos.

    Provides methods for registering, deregistering, discovering,
    and managing service instances.
    """

    pass


class InstanceAsyncEndpoint(_BaseInstanceEndpoint, InstanceAsyncOperationMixin):
    """Asynchronous instance endpoint for Nacos.

    Provides async methods for registering, deregistering, discovering,
    and managing service instances.
    """

    pass